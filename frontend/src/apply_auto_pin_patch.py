#!/usr/bin/env python3
from pathlib import Path
import re
import sys

NEW_HANDLE_SUBMIT = r'''  const handleSubmit = async (e) => {
    e.preventDefault();
    const input = e.target.elements.messageInput;
    const message = input.value.trim();

    if (!message) return;

    const userMessage = { role: 'user', content: message };
    setMessages((prev) => [...prev, userMessage]);
    input.value = '';
    setIsLoading(true);
    setIsTyping(true);

    try {
      let relevantResults = [];

      if (useRag) {
        console.log('RAG is enabled, performing search...');
        const results = await searchRAG(message);

        const relevanceThreshold =
          appConfig?.ui?.components?.search?.relevance_threshold || 0.3;

        relevantResults = results.filter((result) => result.score > relevanceThreshold);

        console.log('Filtered RAG results:', {
          totalResults: results.length,
          relevantResults: relevantResults.length,
          threshold: relevanceThreshold,
          results: relevantResults.map((r) => ({
            score: r.score,
            source: r.source_file,
            preview: r.text.substring(0, 100),
          })),
        });
      } else {
        console.log('RAG is disabled, skipping search');
      }

      const contextMessages = prepareContextMessages(
        messages,
        detailedThinking,
        conversationSummary,
        relevantResults
      );

      let userContent = message;
      if (relevantResults.length > 0) {
        const ragPrefix =
          appConfig?.ui?.chat?.context?.rag_prefix ||
          'Relevant information from knowledge base:\n';
        const ragContext = relevantResults.map((r) => r.text).join('\n\n');
        userContent = `${message}\n\n${ragPrefix}${ragContext}`;
        console.log('Combined user message with RAG context:', userContent);
      }

      contextMessages.push({
        role: 'user',
        content: userContent,
      });

      console.log('Sending context to LLM:', {
        messageCount: contextMessages.length,
        hasRAGContext: relevantResults.length > 0,
        systemMessages: contextMessages.filter((m) => m.role === 'system').length,
        contextPreview: contextMessages.map((m) => ({
          role: m.role,
          contentPreview: m.content.substring(0, 100) + '...',
        })),
      });

      const response = await fetch(`${configLoader.api.llmServer.url}/v1/chat/completions`, {
        method: 'POST',
        headers: {
          ...configLoader.api.llmServer.headers,
          ...(appConfig?.llm?.base_url?.includes(':8002') ? { 'X-LLM-IP': serverIp } : {}),
        },
        body: JSON.stringify({
          model: appConfig?.llm?.model?.name || 'nvidia/Llama-3.1-Nemotron-Nano-4B-v1.1',
          messages: contextMessages,
          stream: false,
          max_tokens: 128,
          temperature: appConfig?.llm?.model?.temperature || 0.6,
          top_p: appConfig?.llm?.model?.top_p || 0.95,
        }),
      });

      if (!response.ok) {
        throw new Error('LLM server is not accessible');
      }

      const data = await response.json();
      const messageContent = data.choices[0].message.content;

      if (!messageContent) {
        throw new Error('Received empty response from LLM server');
      }

      const assistantMessage = {
        role: 'assistant',
        content: messageContent,
        references: useRag ? JSON.stringify(relevantResults) : '',
        showThinking: detailedThinking,
        query: message,
      };

      console.log('Received LLM response:', {
        hasReferences: relevantResults.length > 0,
        referenceCount: relevantResults.length,
        thinkingEnabled: detailedThinking,
        responsePreview: messageContent.substring(0, 100) + '...',
        hasThinkingTags: messageContent.includes('<thinking>'),
      });

      setMessages((prev) => [...prev, assistantMessage]);
      setPictureSearchQuery(message);

      if (usePictures) {
        try {
          const refs = await searchChunks(message, { k: 50 });
          const pictures = await buildPictureResultsFromSearch(message, refs);

          setPictureSearchResults(pictures);

          if (!pictures.length) {
            setPictureSearchError('No matching pictures found for this query.');
          } else {
            setPictureSearchError('');

            const autoPinThreshold =
              appConfig?.ui?.components?.search?.auto_pin_threshold ?? 0.75;

            const bestPicture = [...pictures].sort(
              (a, b) => (b.score || 0) - (a.score || 0)
            )[0];

            if (bestPicture && (bestPicture.score || 0) >= autoPinThreshold) {
              pinPictureToChat(bestPicture);

              setMessages((prev) => {
                const next = [...prev];
                for (let i = next.length - 1; i >= 0; i -= 1) {
                  if (next[i].role === 'assistant') {
                    next[i] = { ...next[i], pinnedPicture: bestPicture };
                    break;
                  }
                }
                return next;
              });
            }
          }
        } catch (pictureError) {
          console.error('Auto picture search failed:', pictureError);
          setPictureSearchResults([]);
          setPictureSearchError('Picture search failed.');
        }
      }

      if ((messages.length + 2) % 3 === 0) {
        const newSummary = await updateSummary([...messages, userMessage, assistantMessage]);
        setConversationSummary(newSummary);
      }
    } catch (error) {
      setIsTyping(false);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: error.message.includes('LLM server is not accessible')
            ? 'The LLM server is not accessible at the moment. Please check if the server is running and try again.'
            : 'Sorry, there was an error processing your request. Please try again.',
          references: '',
          showThinking: detailedThinking,
        },
      ]);
    } finally {
      setIsLoading(false);
      setIsTyping(false);
    }
  };
'''


def patch_app_js(app_js_path: Path) -> None:
    text = app_js_path.read_text(encoding='utf-8')

    pattern = re.compile(
        r"  const handleSubmit = async \(e\) => \{.*?\n  \};\n",
        re.DOTALL,
    )

    if not pattern.search(text):
        raise RuntimeError('Could not find handleSubmit block in App.js')

    updated = pattern.sub(NEW_HANDLE_SUBMIT + "\n", text, count=1)

    if 'auto_pin_threshold' not in updated:
        print('Patched handleSubmit. Add this config manually if needed:')
        print('  "auto_pin_threshold": 0.75')

    app_js_path.write_text(updated, encoding='utf-8')


def main() -> int:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/mnt/data/App.js')
    if not target.exists():
        print(f'File not found: {target}', file=sys.stderr)
        return 1

    patch_app_js(target)
    print(f'Updated {target}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
