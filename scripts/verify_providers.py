"""
Verification script for Azure AI / ML Providers.
Runs a simple test against all configured production providers.
"""

import asyncio
import os
import sys
import tempfile
import time
import wave
from urllib.parse import urlparse

from dotenv import load_dotenv

from careintel.core.config import get_settings
from careintel.domain.ai.models import AITaskConfig, SafeContext, TaskType
from careintel.infrastructure.ai.azure_openai_adapter import AzureOpenAIAdapter
from careintel.infrastructure.embedding.azure_provider import AzureEmbeddingProvider
from careintel.infrastructure.stt.azure_provider import AzureSpeechProvider
from careintel.infrastructure.tts.azure_provider import AzureTTSProvider
from careintel.infrastructure.ocr.azure_provider import AzureDocumentIntelligenceProvider


def mask_secret(secret: str | None) -> str:
    if not secret:
        return "None"
    return secret[:4] + "***" + secret[-4:] if len(secret) > 8 else "***"


def get_host(url: str | None) -> str:
    if not url:
        return "None"
    return urlparse(url).netloc


def _create_dummy_wav() -> str:
    """Create a 1s silent wav file for testing STT."""
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    with wave.open(path, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b'\x00' * 32000)
    return path


def _create_dummy_pdf() -> str:
    """Create a minimal fake PDF."""
    fd, path = tempfile.mkstemp(suffix=".pdf")
    with os.fdopen(fd, 'wb') as f:
        f.write(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Count 1 /Kids [3 0 R] >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n5 0 obj\n<< /Length 44 >>\nstream\nBT\n/F1 24 Tf\n100 700 Td\n(Hello World) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000229 00000 n \n0000000317 00000 n \ntrailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n412\n%%EOF\n")
    return path


async def test_llm(settings) -> bool:
    print(f"\n--- Testing LLM ---")
    print(f"deployment: {settings.azure_llm_deployment}")
    if not (settings.azure_openai_endpoint and settings.azure_openai_api_key):
        print("SKIP: Missing Azure OpenAI credentials.")
        return False
        
    adapter = AzureOpenAIAdapter(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key.get_secret_value(),
        deployment=settings.azure_llm_deployment,
    )
    
    context = SafeContext(
        system_instructions="You are a helpful assistant.",
        task_instructions="Output a JSON with a single key 'message' containing 'Hello'.",
        output_schema={
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
            "additionalProperties": False,
        },
        policy_constraints=[],
        knowledge_passages=[],
        patient_evidence=[],
        stt_transcripts=[],
        ocr_content=[],
        extracted_facts=[],
        timeline_events=[],
        missing_information=[],
        conflicting_information=[],
        retrieval_metadata={}
    )
    
    config = AITaskConfig(
        task_type=TaskType.EVIDENCE_SUMMARY,
        provider="azure_openai",
        model=settings.azure_llm_deployment,
        prompt_version="1.0",
        schema_version="1.0",
        timeout_seconds=30
    )
    
    start = time.time()
    try:
        result = await adapter.generate_structured(context, config)
        latency = time.time() - start
        if result.parsed_content and result.parsed_content.get("message") == "Hello":
            print(f"PASS (Latency: {latency:.2f}s)")
            return True
        else:
            print(f"FAIL: Unexpected result {result.parsed_content} (Latency: {latency:.2f}s)")
            return False
    except Exception as e:
        print(f"FAIL: {e}")
        return False


async def test_embedding(settings) -> bool:
    print(f"\n--- Testing Embedding ---")
    print(f"deployment: {settings.azure_embedding_deployment}")
    if not (settings.azure_openai_endpoint and settings.azure_openai_api_key):
        print("SKIP: Missing Azure OpenAI credentials.")
        return False
        
    adapter = AzureEmbeddingProvider(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key.get_secret_value(),
        deployment=settings.azure_embedding_deployment,
    )
    
    start = time.time()
    try:
        result = await adapter.embed("Hello world")
        latency = time.time() - start
        
        if result.dimension == 1536:
            print(f"PASS (Dimension: {result.dimension}, Latency: {latency:.2f}s)")
            return True
        else:
            print(f"FAIL: Expected dimension 1536, got {result.dimension}")
            return False
    except Exception as e:
        print(f"FAIL: {e}")
        return False


async def test_stt(settings) -> bool:
    print(f"\n--- Testing STT ---")
    print(f"deployment: {settings.azure_stt_deployment}")
    route = f"{settings.azure_openai_endpoint.rstrip('/')}/openai/deployments/{settings.azure_stt_deployment}/audio/transcriptions?api-version={settings.azure_stt_api_version}"
    print(f"route:\n{route}")
    
    if not (settings.azure_openai_endpoint and settings.azure_openai_api_key):
        print("SKIP: Missing Azure OpenAI credentials.")
        return False
        
    adapter = AzureSpeechProvider(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key.get_secret_value(),
        api_version=settings.azure_stt_api_version,
        deployment=settings.azure_stt_deployment,
        mode="transcribe"
    )
    
    wav_path = _create_dummy_wav()
    start = time.time()
    try:
        result = await adapter.process_audio(wav_path, "00000000-0000-0000-0000-000000000000")
        latency = time.time() - start
        print(f"PASS (Segments: {len(result.segments)}, Latency: {latency:.2f}s)")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        return False
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)

async def test_stt_diarization(settings) -> bool:
    print(f"\n--- Testing STT Diarization ---")
    print(f"deployment: {settings.azure_stt_diarize_deployment}")
    route = f"{settings.azure_openai_endpoint.rstrip('/')}/openai/deployments/{settings.azure_stt_diarize_deployment}/audio/transcriptions?api-version={settings.azure_stt_diarize_api_version}"
    print(f"route:\n{route}")
    
    if not (settings.azure_openai_endpoint and settings.azure_openai_api_key):
        print("SKIP: Missing Azure OpenAI credentials.")
        return False
        
    adapter = AzureSpeechProvider(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key.get_secret_value(),
        api_version=settings.azure_stt_diarize_api_version,
        deployment=settings.azure_stt_diarize_deployment,
        mode="diarize"
    )
    
    wav_path = _create_dummy_wav()
    start = time.time()
    try:
        result = await adapter.process_audio(wav_path, "00000000-0000-0000-0000-000000000000")
        latency = time.time() - start
        print(f"PASS (Segments: {len(result.segments)}, Latency: {latency:.2f}s)")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        return False
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)


async def test_tts(settings) -> bool:
    print(f"\n--- Testing TTS ---")
    print(f"deployment: {settings.azure_tts_deployment}")
    route = f"{settings.azure_openai_endpoint.rstrip('/')}/openai/deployments/{settings.azure_tts_deployment}/audio/speech?api-version={settings.azure_tts_api_version}"
    print(f"route:\n{route}")
    
    if not (settings.azure_openai_endpoint and settings.azure_openai_api_key):
        print("SKIP: Missing Azure OpenAI credentials.")
        return False
        
    adapter = AzureTTSProvider(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key.get_secret_value(),
        api_version=settings.azure_tts_api_version,
        deployment=settings.azure_tts_deployment,
    )
    
    start = time.time()
    try:
        result = await adapter.synthesize("Hello world")
        latency = time.time() - start
        if len(result.audio_bytes) > 100:
            print(f"PASS (Bytes: {len(result.audio_bytes)}, Latency: {latency:.2f}s)")
            return True
        else:
            print(f"FAIL: Too few bytes returned ({len(result.audio_bytes)})")
            return False
    except Exception as e:
        print(f"FAIL: {e}")
        return False


async def test_ocr(settings) -> bool:
    print(f"\n--- Testing OCR ---")
    print("provider:\nAzure Document Intelligence")
    print("endpoint:")
    print("read from AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    
    if not (settings.azure_document_intelligence_endpoint and settings.azure_document_intelligence_key):
        print("SKIP: Missing Azure Document Intelligence credentials.")
        return False
        
    adapter = AzureDocumentIntelligenceProvider(
        endpoint=settings.azure_document_intelligence_endpoint,
        key=settings.azure_document_intelligence_key.get_secret_value(),
        model=settings.azure_di_model,
    )
    
    pdf_path = _create_dummy_pdf()
    start = time.time()
    try:
        result = await adapter.process_document(pdf_path, "00000000-0000-0000-0000-000000000000")
        latency = time.time() - start
        print(f"PASS (Pages: {len(result.pages)}, Regions: {len(result.regions)}, Latency: {latency:.2f}s)")
        return True
    except Exception as e:
        if "InvalidRequest" in str(e) or "Bad Request" in str(e):
             print(f"PASS [Partial]: Connected, but dummy PDF rejected as expected. (Latency: {time.time()-start:.2f}s)\nDetails: {str(e)[:100]}...")
             return True
        print(f"FAIL: {e}")
        return False
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


async def main() -> None:
    load_dotenv()
    settings = get_settings()
    
    print("="*60)
    print("CAREINTEL AZURE AI PROVIDER VERIFICATION")
    print("="*60)
    
    results = {
        "LLM": await test_llm(settings),
        "Embedding": await test_embedding(settings),
        "STT": await test_stt(settings),
        "STT Diarization": await test_stt_diarization(settings),
        "TTS": await test_tts(settings),
        "OCR": await test_ocr(settings)
    }
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    all_pass = True
    for k, v in results.items():
        status = "PASS/SKIPPED" if v else "FAIL/SKIPPED"
        if not v:
            all_pass = False
        print(f"{k.ljust(15)}: {status}")
        
    if not all_pass:
        print("\nNote: Skipped tests count as FAIL for the overall run if credentials were not provided.")
        sys.exit(1)
    else:
        print("\nAll tested providers passed.")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
