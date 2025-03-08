## Chat Context Management

[source](https://github.com/livekit/agents/blob/dev-1.0/livekit-agents/livekit/agents/llm/chat_context.py)

Core class for managing conversation history and function calling state.

### Class Definition

```python
class ChatContext:
    def __init__(self, messages: list[ChatMessage], functions: list[AIFunction]):
        self.messages = messages
        self.functions = functions

    @classmethod
    def empty(cls) -> ChatContext:
        """Create empty chat context"""
    
    def copy(self) -> ChatContext:
        """Create a deep copy of the context"""
    
    def trim_messages(
        self,
        max_messages: int | None = None,
        max_tokens: int | None = None,
        tokenizer: Tokenizer = default_tokenizer(),
    ) -> None:
        """Trim conversation history based on limits"""
```

### Message Types

```python
class ChatMessage:
    class Role(Enum):
        SYSTEM = "system"
        USER = "user"
        ASSISTANT = "assistant"
        FUNCTION = "function"

    role: Role
    name: str | None  # For function messages
    content: str | None
    function_call: FunctionCall | None  # For assistant messages
```

### Key Methods

| Method                          | Description                                  |
|---------------------------------|----------------------------------------------|
| `add_system_message(content)`   | Add system prompt/instructions              |
| `add_user_message(content)`     | Add user query                               |
| `add_assistant_message(content, function_call)` | Add LLM response |
| `add_function_result(name, result)` | Add function call result              |
| `clear_messages()`              | Reset conversation history                   |
| `merge(other_ctx)`              | Combine with another context                 |

### Usage Example

```python
# Create new context with system message
ctx = ChatContext.empty()
ctx.add_system_message("You're a helpful assistant")

# Conversation flow
ctx.add_user_message("What's the weather in Paris?")
ctx.add_assistant_message(
    None,
    function_call=FunctionCall(name="get_weather", arguments={"location": "Paris"})
)
ctx.add_function_result("get_weather", "Sunny, 22°C")

# Trim to last 2 messages
ctx.trim_messages(max_messages=2)
```

### Best Practices

1. Start with clear system instructions
2. Include function results in history for context
3. Use trim_messages() to manage token limits
4. Clone contexts for branching conversations
5. Add metadata via hidden system messages
6. Validate function call arguments before execution

### Advanced Features

- **Context Branching:** Create conversation variants using copy()
- **Token Counting:** Integrate custom tokenizers
- **Selective Merging:** Combine relevant history from multiple contexts
- **Message Metadata:** Store additional data in message objects
- **Function Call Chaining:** Handle sequential function executions

