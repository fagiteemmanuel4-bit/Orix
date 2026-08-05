Source: https://github.com/nidhinjs/prompt-master

Summary:
- Purpose: structured prompt generation pipeline that detects target tool, extracts intent across dimensions (task, input, constraints, context, examples), asks clarifying questions when needed, and outputs a concise token-efficient prompt.
- Notable features: routing to tool-specific templates, memory block handling, and a token-efficiency audit.

Reusable patterns:
- Memory block header for carrying previous decisions.
- 9-dimension intent extractor (task, input, output, constraints, context, audience, memory, success criteria, examples).
- Prompt templates for image and code tasks (use as examples for `ai_builder` prompt generation).
