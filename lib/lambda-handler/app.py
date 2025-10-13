import json

def handler(event, context):
    # Extract specific properties from the event object
    resource = event.get('resource')
    path = event.get('path')
    http_method = event.get('httpMethod')
    headers = event.get('headers')
    query_string_parameters = event.get('queryStringParameters')
    body = event.get('body')
    
    response = {
        'resource': resource,
        'path': path,
        'httpMethod': http_method,
        'headers': headers,
        'queryStringParameters': query_string_parameters,
        'body': body,
    }
    
    return {
        'body': json.dumps(response, indent=2),
        'statusCode': 200,
    }


