from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional

import ollama
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import get_settings
from app.rag.retriever import VectorRetriever
from app.storage.models import UserProfile
from app.storage.mongo import get_content_by_id

settings = get_settings()

AGENT_SYSTEM_PROMPT = """You are Q-Rater, a personalized content intelligence assistant. You help users discover, search, and get insights from a library of ingested YouTube and Instagram video content.

You have access to two tools:
1. `search_content` — semantic search over the video library
2. `get_content_detail` — retrieve full transcript and comments for a specific content item

When answering user queries:
- Use `search_content` to find relevant videos
- Use `get_content_detail` when you need deeper context about a specific item
- Synthesize information from multiple sources when helpful
- Always cite the source titles and URLs in your final answer
- Be conversational and helpful, not robotic"""

# Ollama uses OpenAI-style tool definitions: type=function with a nested "function" key
TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_content",
            "description": "Semantic search over the ingested video content library. Returns the most relevant content items for the given query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query describing what content to find",
                    },
                    "source_filter": {
                        "type": "string",
                        "enum": ["youtube", "instagram", "any"],
                        "description": "Filter by platform. Use 'any' for no filter.",
                    },
                    "content_type_filter": {
                        "type": "string",
                        "description": "Optional content type filter (e.g., 'tutorial', 'review', 'entertainment')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results to return (1-20)",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_content_detail",
            "description": "Retrieve the full transcript and top comments for a specific content item by its content_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content_id": {
                        "type": "string",
                        "description": "The content_id of the item to retrieve",
                    },
                },
                "required": ["content_id"],
            },
        },
    },
]


@dataclass
class AgentResponse:
    answer: str
    sources: list[dict] = field(default_factory=list)
    iterations: int = 0


class RAGAgent:
    def __init__(self, retriever: VectorRetriever, db: AsyncIOMotorDatabase) -> None:
        self._client: ollama.AsyncClient | None = None
        self.retriever = retriever
        self.db = db
        self._sources: list[dict] = []

    def _get_client(self) -> ollama.AsyncClient:
        if self._client is None:
            self._client = ollama.AsyncClient(host=settings.ollama_base_url)
        return self._client

    async def query(
        self,
        user_query: str,
        user_profile: Optional[UserProfile] = None,
        max_iterations: int = 5,
    ) -> AgentResponse:
        self._sources = []
        system = self._build_system(user_profile)

        messages: list[dict] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_query},
        ]

        for iteration in range(max_iterations):
            response = await self._get_client().chat(
                model=settings.ollama_model,
                messages=messages,
                tools=TOOLS,
            )

            msg = response.message

            # No tool calls — model produced a final answer
            if not msg.tool_calls:
                return AgentResponse(
                    answer=msg.content or "",
                    sources=self._sources,
                    iterations=iteration + 1,
                )

            # Append the assistant turn (with tool calls) to the history
            messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": [
                {
                    "id": tc.function.name,  # Ollama doesn't always provide an ID; use name
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": json.dumps(tc.function.arguments),
                    },
                }
                for tc in msg.tool_calls
            ]})

            # Execute each tool call and append results
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                fn_args = tc.function.arguments  # already a dict from Ollama

                tool_output = await self._call_tool(fn_name, fn_args)

                # Tool results go back as role=tool messages
                messages.append({
                    "role": "tool",
                    "content": tool_output,
                    "name": fn_name,
                })

        return AgentResponse(
            answer="I was unable to find a satisfactory answer. Please try rephrasing your query.",
            sources=self._sources,
            iterations=max_iterations,
        )

    async def _call_tool(self, name: str, args: dict) -> str:
        if name == "search_content":
            try:
                hits = await self.retriever.search(
                    query=args.get("query", ""),
                    source_filter=args.get("source_filter"),
                    content_type_filter=args.get("content_type_filter"),
                    limit=min(int(args.get("limit", 5)), 20),
                )
                self._sources.extend(hits)
                return json.dumps(hits, default=str)
            except Exception as exc:
                return json.dumps({"error": str(exc)})

        if name == "get_content_detail":
            try:
                doc = await get_content_by_id(self.db, args.get("content_id", ""))
                if doc:
                    detail = {
                        "content_id": doc.get("content_id"),
                        "title": doc.get("metadata", {}).get("title", ""),
                        "transcript": doc.get("raw", {}).get("transcript", "")[:3000],
                        "comments": doc.get("raw", {}).get("comments", [])[:20],
                        "summary": doc.get("summary", {}),
                    }
                else:
                    detail = {"error": "Content not found"}
                return json.dumps(detail, default=str)
            except Exception as exc:
                return json.dumps({"error": str(exc)})

        return json.dumps({"error": f"Unknown tool: {name}"})

    @staticmethod
    def _build_system(user_profile: Optional[UserProfile]) -> str:
        system = AGENT_SYSTEM_PROMPT
        if user_profile and user_profile.interests:
            interests_str = ", ".join(user_profile.interests)
            system += f"\n\nUser interests: {interests_str}. Prioritize content aligned with these interests when multiple results are equally relevant."
        return system
