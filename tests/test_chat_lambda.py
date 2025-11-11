import json
import os
import sys
from types import SimpleNamespace


# Ensure project root is importable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.chat import chat as chat_module  # noqa: E402


class FakeTable:
    def __init__(self, name, stores, aptitudes_items=None):
        self.name = name
        self.stores = stores
        self.aptitudes_items = aptitudes_items or []

    def scan(self, **kwargs):
        if self.name == chat_module.APTITUDES_TABLE_NAME:
            return {"Items": self.aptitudes_items}
        raise AssertionError("scan only supported for aptitudes table in tests")

    def get_item(self, Key):
        if self.name == chat_module.PROGRESS_TABLE_NAME:
            item = self.stores["progress"].get(Key.get("ChatID"))
            return {"Item": item} if item else {}
        raise AssertionError("get_item only supported for progress table in tests")

    def put_item(self, Item):
        if self.name == chat_module.PROGRESS_TABLE_NAME:
            self.stores["progress"][Item["ChatID"]] = Item
            return {"ResponseMetadata": {"HTTPStatusCode": 200}}
        raise AssertionError("put_item only supported for progress table in tests")

    def update_item(self, Key, UpdateExpression=None, ConditionExpression=None,
                    ExpressionAttributeNames=None, ExpressionAttributeValues=None, ReturnValues=None):
        # Used for quota tracking; maintain a simple in-memory counter per (UserID, Date)
        if self.name == chat_module.QUOTA_TABLE_NAME:
            user_id = Key.get("UserID")
            date = Key.get("Date")
            quota_key = (user_id, date)
            current = self.stores["quota"].get(quota_key, {"Count": 0})
            increment = ExpressionAttributeValues.get(":inc", 0)
            decrement = ExpressionAttributeValues.get(":dec", 0) if ExpressionAttributeValues else 0
            if ":inc" in ExpressionAttributeValues:
                current["Count"] = current.get("Count", 0) + increment
            if ":dec" in (ExpressionAttributeValues or {}):
                current["Count"] = current.get("Count", 0) - decrement
            self.stores["quota"][quota_key] = current
            return {"Attributes": current} if ReturnValues == "UPDATED_NEW" else {}
        raise AssertionError("update_item only supported for quota table in tests")


class FakeDynamoResource:
    def __init__(self, stores, aptitudes):
        self.stores = stores
        # Convert to items structure expected by scan
        self.aptitudes_items = [{"aptitud": a, "activa": True} for a in aptitudes]

    def Table(self, name):
        if name == chat_module.APTITUDES_TABLE_NAME:
            return FakeTable(name, self.stores, self.aptitudes_items)
        if name == chat_module.PROGRESS_TABLE_NAME:
            return FakeTable(name, self.stores)
        if name == chat_module.QUOTA_TABLE_NAME:
            return FakeTable(name, self.stores)
        raise AssertionError(f"Unexpected table requested: {name}")


class FakeBedrockClient:
    def __init__(self, non_final_text="Pregunta generada", conclusion_text="Conclusión final"):
        self.non_final_text = non_final_text
        self.conclusion_text = conclusion_text

    def invoke_model(self, modelId, body, accept, contentType):
        payload = json.loads(body)
        # Final analysis path when toolConfig present
        if "toolConfig" in payload:
            response_body = {
                "output": {
                    "message": {
                        "content": [
                            {
                                "toolUse": {
                                    "input": {
                                        "conclusion": self.conclusion_text,
                                        "aptitudes_scores": {"Aptitud 1": 8, "Aptitud 2": 6}
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        else:
            response_body = {
                "output": {
                    "message": {
                        "content": [
                            {"text": self.non_final_text}
                        ]
                    }
                }
            }

        class Body:
            def __init__(self, data):
                self._data = data

            def read(self):
                return json.dumps(self._data)

        return {"body": Body(response_body)}


def make_event(chat_id, user_id=None, prompt="mi respuesta"):
    body = {"ChatID": chat_id}
    if user_id:
        body["UserID"] = user_id
    body["prompt"] = prompt
    return {
        "httpMethod": "POST",
        "body": json.dumps(body)
    }


def test_initial_flow_persists_total_questions_and_waiting_q2(monkeypatch):
    stores = {"progress": {}, "quota": {}}
    aptitudes = [f"Aptitud {i}" for i in range(1, 8)]  # 7 aptitudes

    # Patch module clients
    chat_module.dynamodb = FakeDynamoResource(stores, aptitudes)
    chat_module.bedrock = FakeBedrockClient(non_final_text="Primera pregunta")

    event = make_event(chat_id="chat-1", user_id="user-1")
    result = chat_module.handler(event, context={})

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["status"] == "Waiting for 2 of 7"
    assert body["chatbot_response"] == "Primera pregunta"

    # Verify progress was persisted with TotalQuestions = 7 and QuestionNumber = 2
    persisted = stores["progress"]["chat-1"]
    assert persisted["TotalQuestions"] == 7
    assert persisted["QuestionNumber"] == 2

    # Now call again with no prompt to retrieve history (chat in progress)
    event_no_prompt = {
        "httpMethod": "POST",
        "body": json.dumps({"ChatID": "chat-1", "UserID": "user-1"})
    }
    result2 = chat_module.handler(event_no_prompt, context={})
    assert result2["statusCode"] == 200
    body2 = json.loads(result2["body"])
    assert body2["status"] == "Waiting for 2 of 7"
    # Should not change QuestionNumber nor append new assistant message
    persisted2 = stores["progress"]["chat-1"]
    assert persisted2["QuestionNumber"] == 2


def test_final_analysis_after_all_questions_and_returns_scores(monkeypatch):
    stores = {"progress": {}, "quota": {}}
    aptitudes = [f"Aptitud {i}" for i in range(1, 6)]  # 5 aptitudes

    chat_module.dynamodb = FakeDynamoResource(stores, aptitudes)
    chat_module.bedrock = FakeBedrockClient(conclusion_text="Conclusión final sintetizada")

    # First call to initialize and move to Q2
    result1 = chat_module.handler(make_event(chat_id="chat-2", user_id="user-2"), context={})
    assert result1["statusCode"] == 200

    # Simulate that we're at the last question just answered; next_question == TotalQuestions
    item = stores["progress"]["chat-2"]
    item["QuestionNumber"] = item["TotalQuestions"]  # trigger >= condition
    stores["progress"]["chat-2"] = item

    # Next call should trigger final analysis
    result2 = chat_module.handler(make_event(chat_id="chat-2", user_id="user-2", prompt="última respuesta"), context={})
    assert result2["statusCode"] == 200
    body2 = json.loads(result2["body"])
    assert body2["status"] == "FINISHED"
    assert body2["chatbot_response"] == "Conclusión final sintetizada"
    assert "final_scores" in body2
    assert isinstance(body2["final_scores"], dict)


def test_cap_at_100_aptitudes(monkeypatch):
    stores = {"progress": {}, "quota": {}}
    aptitudes = [f"Aptitud {i}" for i in range(1, 151)]  # 150 -> cap to 100

    chat_module.dynamodb = FakeDynamoResource(stores, aptitudes)
    chat_module.bedrock = FakeBedrockClient(non_final_text="Pregunta con cap")

    result = chat_module.handler(make_event(chat_id="chat-3", user_id="user-3"), context={})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["status"] == "Waiting for 2 of 100"
    assert body["chatbot_response"] == "Pregunta con cap"

    # Verify cap applied
    persisted = stores["progress"]["chat-3"]
    assert persisted["TotalQuestions"] == min(150, chat_module.MAX_QUESTIONS) == 100
    # Ensure the master prompt in history references the capped count
    master_prompt = persisted["History"][0]
    assert f"({persisted['TotalQuestions']} Preguntas" in master_prompt


def test_rejects_overly_long_user_input_with_400(monkeypatch):
    stores = {"progress": {}, "quota": {}}
    aptitudes = [f"Aptitud {i}" for i in range(1, 4)]
    from lib.chat import chat as chat_module_local
    chat_module_local.dynamodb = FakeDynamoResource(stores, aptitudes)
    chat_module_local.bedrock = FakeBedrockClient()

    long_text = "x" * (chat_module_local.MAX_USER_INPUT_CHARS + 50)
    event = make_event(chat_id="chat-4", user_id="user-4", prompt=long_text)
    result = chat_module_local.handler(event, context={})
    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert "excede el máximo" in body.get("error", "").lower()


