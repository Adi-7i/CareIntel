"""
Phase 5 Demo Script.
Simulates triggering multimodal processing for Evidence.
"""

import asyncio
import os
import uuid

import httpx


async def run_demo() -> None:
    print("CareIntel Phase 5 - Multimodal Processing Demo")
    base_url = os.getenv("API_URL", "http://localhost:8000/api/v1")
    token = os.getenv("AUTH_TOKEN")

    if not token:
        print("Warning: AUTH_TOKEN not set. Skipping real API call simulation.")
        print("Set AUTH_TOKEN and run again to hit the local server.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    evidence_id = str(uuid.uuid4())  # In reality, get this from an uploaded evidence

    async with httpx.AsyncClient(base_url=base_url, headers=headers) as client:
        # Trigger OCR
        print(f"\n[1] Triggering Document OCR for evidence: {evidence_id}")
        resp = await client.post(
            "/processing/trigger",
            json={"evidence_id": evidence_id, "processor_type": "document_ocr"},
        )
        if resp.status_code == 202:
            run_id = resp.json().get("run_id")
            print(f" -> Success! Run ID: {run_id}")
        else:
            print(f" -> Failed: {resp.text}")

        # Trigger STT
        print(f"\n[2] Triggering Speech Transcription for evidence: {evidence_id}")
        resp = await client.post(
            "/processing/trigger",
            json={"evidence_id": evidence_id, "processor_type": "speech_transcription"},
        )
        if resp.status_code == 202:
            run_id = resp.json().get("run_id")
            print(f" -> Success! Run ID: {run_id}")
        else:
            print(f" -> Failed: {resp.text}")

        # Trigger Extraction
        print(f"\n[3] Triggering Candidate Extraction for evidence: {evidence_id}")
        resp = await client.post(
            "/processing/trigger",
            json={
                "evidence_id": evidence_id,
                "processor_type": "candidate_extraction",
                "parameters": {"text": "Patient has a fever"},
            },
        )
        if resp.status_code == 202:
            run_id = resp.json().get("run_id")
            print(f" -> Success! Run ID: {run_id}")
        else:
            print(f" -> Failed: {resp.text}")


if __name__ == "__main__":
    asyncio.run(run_demo())
