"""Scripted ADK lifecycle fixtures. Never use as training or model evidence."""

import asyncio

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from pydantic import PrivateAttr

from zenithsync.artifacts import canonical_json


class SourceRunnerFixture(BaseLlm):
    scenario: str
    _requests: list = PrivateAttr(default_factory=list)
    _calls: int = PrivateAttr(default=0)
    _output: object = PrivateAttr(default=None)

    def retain_to(self, output):
        self._output = output

    async def generate_content_async(self, llm_request, stream=False):
        self._calls += 1
        self._requests.append(llm_request.model_dump(mode='json', exclude_none=True))
        self._output.write_bytes(canonical_json({'fixture': self.scenario,
            'synthetic_usage': True, 'training_approved': False, 'requests': self._requests}))
        if self.scenario == 'timeout':
            await asyncio.sleep(3600)
            raise AssertionError('Timeout fixture unexpectedly completed')
        if self.scenario == 'turn-limit':
            name, arguments = 'run_command', {'command': 'true'}
        elif self._calls == 1:
            name, arguments = 'write_file', {'filepath': 'diagnostic.txt',
                'content': 'OFFLINE LIFECYCLE FIXTURE; NOT A REPAIR\n'}
        elif self._calls == 2:
            name, arguments = 'submit_patch', {}
        elif self.scenario == 'submit-then-fail':
            raise RuntimeError('Intentional offline failure after submission')
        else:
            yield LlmResponse(content=types.Content(role='model', parts=[
                types.Part(text='Offline lifecycle fixture complete; no repair performed.')]))
            return
        yield LlmResponse(content=types.Content(role='model', parts=[
            types.Part(function_call=types.FunctionCall(name=name, args=arguments,
                                                      id=f'fixture_{self._calls}'))]),
            usage_metadata=types.GenerateContentResponseUsageMetadata(
                prompt_token_count=100, candidates_token_count=1, total_token_count=101))
