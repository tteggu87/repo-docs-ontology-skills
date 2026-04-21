class EmbeddingService:
    async def auto_embed_entity(self, entity_id: str) -> dict[str, str]:
        return {"entity_id": entity_id, "status": "embedded"}
