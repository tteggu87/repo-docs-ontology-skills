from pkg_intelligence.embedding_service import EmbeddingService


async def _handle_generate_v_atomic(payload: dict[str, str]) -> dict[str, str]:
    service = EmbeddingService()
    return await service.auto_embed_entity(payload["entity_id"])
