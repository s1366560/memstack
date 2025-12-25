from graphiti_core.prompts.models import EntityResolution
import json

print(json.dumps(EntityResolution.model_json_schema(), indent=2))
