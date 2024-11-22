import json
from typing import Any, Sequence, Tuple, Union
from vllm.entrypoints.openai.protocol import (ChatCompletionRequest,
                                              DeltaFunctionCall, DeltaMessage,
                                              DeltaToolCall,
                                              ExtractedToolCallInformation,
                                              FunctionCall, ToolCall)
from vllm.entrypoints.openai.tool_parsers.abstract_tool_parser import (
    ToolParser, ToolParserManager)
from vllm.logger import init_logger
from vllm.transformers_utils.tokenizer import AnyTokenizer

logger = init_logger(__name__)


@ToolParserManager.register_module("functionary_32")
class Functionary32ToolParser(ToolParser):

    # TODO: tool call regex

    def __init__(self, tokenizer: AnyTokenizer):
        super().__init__(tokenizer)
        logger.warn("A streaming tool parser has not been implemented for functionary 3.2. Expect regular text "
                    "completions for streaming requests.")

    def extract_tool_calls(
            self, model_output: str,
            request: ChatCompletionRequest) -> ExtractedToolCallInformation:
        return ExtractedToolCallInformation(
            tools_called=False,
            tool_calls=[],
            content=model_output
        )

    def extract_tool_calls_streaming(
            self,
            previous_text: str,
            current_text: str,
            delta_text: str,
            previous_token_ids: Sequence[int],
            current_token_ids: Sequence[int],
            delta_token_ids: Sequence[int],
            request: ChatCompletionRequest,
    ) -> Union[DeltaMessage, None]:
        return DeltaMessage(content=delta_text)