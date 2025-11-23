#!/usr/bin/env python3
"""
Test the external research worker locally using TEST_MODE.

This script:
- Calls the external research handler directly (no Lambda invocations)
- Skips DynamoDB operations (no AWS connection needed)
- Only requires ANTHROPIC_API_KEY

Usage:
    export TEST_MODE=true
    export ANTHROPIC_API_KEY='your-key-here'
    python3 test_external_research_worker_locally.py
"""
import json
import os
import sys

# Import the external research handler after environment setup
# (This is done here to ensure TEST_MODE is set before import)
from external_research_worker import handler

# Check environment
if not os.environ.get('ANTHROPIC_API_KEY'):
    print("❌ ERROR: ANTHROPIC_API_KEY not set")
    print("Please run: export ANTHROPIC_API_KEY='your-key-here'")
    sys.exit(1)

print("\n" + "=" * 70)
print("  TESTING EXTERNAL RESEARCH WORKER IN TEST_MODE (Local, No AWS)")
print("=" * 70)
print("\n✓ TEST_MODE enabled - using direct handler calls")
print("✓ Skipping DynamoDB operations")
print("✓ No Lambda invocations - calling handlers directly\n")

# Test external research parameters
expert_profile = "Especialista en ciberseguridad y protección anti-spam con experiencia en telecomunicaciones"
questions = [
    "¿Cuáles son las mejores prácticas para implementar filtros anti-spam a nivel de operador?",
    "¿Qué tecnologías emergentes existen para detectar y bloquear comunicaciones spam?",
    "¿Cómo implementar un sistema de reputación para números telefónicos?"
]
context_summary = """
En Chile hay una cantidad alta de comunicaciones de spam que causa dolores
en la vida de todos los chilenos. Queremos atacar este problema con una solución
tecnológica que incluya filtros avanzados y sistemas de reputación.
""".strip()

if len(sys.argv) > 1:
    expert_profile = " ".join(sys.argv[1:])
    print("📋 Using custom expert profile from command line")

print("📋 BÚSQUEDA DE EXPERTO EXTERNO:")
print(f"   Perfil: {expert_profile}")
print(f"   Preguntas: {len(questions)} preguntas preparadas")
print(f"   Contexto: {context_summary[:100]}...\n")

# Create test event (TEST_MODE format for external research)
event = {
            "instructions":
            {
                "expert_profile": expert_profile,
                "questions": questions,
                "context_summary": context_summary
            }
        }

print("🚀 Calling external research handler...")
print("-" * 70)

try:
    # Call the handler
    response = handler(event, None)

    print("\n" + "=" * 70)
    print("  ✅ EXTERNAL RESEARCH COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print("response: ", response)
    print("type of response: ", type(response))

    # Check response structure
    if not response:
        print("❌ ERROR: Handler returned None")
        sys.exit(1)

    if not isinstance(response, dict):
        print(f"❌ ERROR: Handler returned {type(response)}, expected dict")
        sys.exit(1)

    if 'body' not in response:
        print(f"❌ ERROR: Response missing 'body' field. Keys: {response.keys()}")
        sys.exit(1)

    print(f"Response body: {response['body']}")
    print(f"Body type: {type(response['body'])}")

    if not response['body']:
        print("❌ ERROR: Response body is empty")
        sys.exit(1)

    # Parse response
    try:
        body = json.loads(response['body'])
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Failed to parse response body as JSON: {e}")
        print(f"Raw body content: {repr(response['body'])}")
        sys.exit(1)
    result = body.get('result', {})

    print("\n📊 RESULTADO:")
    print(f"   Status Code: {response['statusCode']}")
    print(f"   Message: {body.get('message', 'N/A')}")

    if result:
        print("\n✓ Expertos encontrados:")
        experts = result.get('found_experts', [])
        print(f"   - Total: {len(experts)} expertos")
        for expert in experts[:3]:  # Show first 3
            print(f"   - {expert.get('name', 'N/A')} ({expert.get('source', 'N/A')})")

        recommendations = result.get('recommendations', [])
        high_priority = [r for r in recommendations if r.get('recommend_contact', False)]
        print(f"\n✓ Recomendaciones: {len(high_priority)} expertos recomendados para contacto")
        print(f"✓ Generado en: {result.get('generated_at', 'N/A')}")

        # Save to file
        output_file = f"external_research_result_{os.getpid()}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n📁 Resultado completo guardado en: {output_file}")

        # Show search summary
        summary = result.get('search_summary', '')
        if summary:
            print("\n" + "=" * 70)
            print("  RESUMEN DE BÚSQUEDA")
            print("=" * 70)
            print(summary)
            print("-" * 70)

    print("\n✅ Test completado exitosamente!")

except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    print("\n" + traceback.format_exc())
    sys.exit(1)
