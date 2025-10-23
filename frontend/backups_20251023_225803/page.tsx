/**
 * Main Chat Interface for Myk Raws Legal RAG
 * Handles user queries and displays responses with context
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { Send, FileText, Scale, AlertCircle, CheckCircle, Loader2, ThumbsUp, ThumbsDown } from 'lucide-react';
import { chatAPI, QueryResponse, ContextDocument, handleAPIError } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  response?: QueryResponse;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => crypto.randomUUID());
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle query submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      type: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await chatAPI.query({
        query: input,
        session_id: sessionId,
        include_interpretive_cases: true,
        max_results: 10,
        enable_synthesis: true,
      });

      const assistantMessage: Message = {
        id: crypto:randomUUID(),
        type: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        response,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      setError(handleAPIError(err));
      console.error('Query failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle feedback
  const handleFeedback = async (queryId: string, rating: number) => {
    try {
      await chatAPI.submitFeedback(queryId, rating);
    } catch (err) {
      console.error('Feedback failed:', err);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center gap-3">
          <Scale className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Myk Raws Legal AI</h1>
            <p className="text-sm text-gray-600">Singapore Statutory Interpretation Assistant</p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        <div className="max-w-6xl mx-auto h-full flex flex-col px-6 py-4">
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto space-y-4 mb-4">
            {messages.length === 0 ? (
              <EmptyState />
            ) : (
              messages.map((message) => (
                <MessageCard
                  key={message.id}
                  message={message}
                  onFeedback={handleFeedback}
                />
              ))
            )}
            {isLoading && <LoadingMessage />}
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a legal question... (e.g., 'What are the remedies for misrepresentation under contract law?')"
              className="min-h-[100px] border-0 focus:ring-0 resize-none"
              disabled={isLoading}
            />
            <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-100">
              <p className="text-xs text-gray-500">
                Press Enter to send • Shift+Enter for new line
              </p>
              <Button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    Send
                  </>
                )}
              </Button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}

// === COMPONENTS ===

function EmptyState() {
  const exampleQueries = [
    "What are the remedies available for misrepresentation under Singapore contract law?",
    "Explain the test for determining if conduct is 'plain and obvious' under ROC 2021.",
    "What is the penalty for breach of fiduciary duty?",
  ];

  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-4">
      <Scale className="w-16 h-16 text-blue-600 mb-4" />
      <h2 className="text-2xl font-semibold text-gray-900 mb-2">
        Ask a Legal Question
      </h2>
      <p className="text-gray-600 mb-8 max-w-md">
        Get instant answers backed by Singapore statutes and case law with interpretation analysis
      </p>
      <div className="space-y-2 w-full max-w-2xl">
        <p className="text-sm font-medium text-gray-700 mb-3">Try asking:</p>
        {exampleQueries.map((query, i) => (
          <button
            key={i}
            className="w-full text-left p-3 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors text-sm"
            onClick={() => {
              const textarea = document.querySelector('textarea');
              if (textarea) {
                textarea.value = query;
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
              }
            }}
          >
            {query}
          </button>
        ))}
      </div>
    </div>
  );
}

function LoadingMessage() {
  return (
    <Card className="bg-blue-50 border-blue-200">
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
          <div>
            <p className="font-medium text-blue-900">Processing your query...</p>
            <p className="text-sm text-blue-700">Retrieving statutes and case law</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface MessageCardProps {
  message: Message;
  onFeedback: (queryId: string, rating: number) => void;
}

function MessageCard({ message, onFeedback }: MessageCardProps) {
  if (message.type === 'user') {
    return (
      <div className="flex justify-end">
        <Card className="max-w-2xl bg-blue-600 text-white">
          <CardContent className="p-4">
            <p className="whitespace-pre-wrap">{message.content}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const response = message.response;
  if (!response) return null;

  return (
    <div className="space-y-3">
      {/* Main Answer */}
      <Card>
        <CardContent className="p-6">
          <div className="prose max-w-none">
            <div className="whitespace-pre-wrap">{response.answer}</div>
          </div>

          {/* Quality Metrics */}
          <div className="flex items-center gap-4 mt-4 pt-4 border-t border-gray-100">
            <QualityBadge
              label="Quality"
              value={response.quality_metrics.synthesis_quality}
            />
            <QualityBadge
              label="Citation"
              value={response.quality_metrics.citation_precision}
            />
            {response.interpretation_links_used > 0 && (
              <Badge variant="secondary">
                {response.interpretation_links_used} Interpretive Cases
              </Badge>
            )}
            <span className="text-xs text-gray-500 ml-auto">
              {response.processing_time.toFixed(2)}s
            </span>
          </div>

          {/* Warnings */}
          {response.warnings.length > 0 && (
            <Alert className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {response.warnings.join('; ')}
              </AlertDescription>
            </Alert>
          )}

          {/* Feedback */}
          <div className="flex items-center gap-2 mt-4 pt-4 border-t border-gray-100">
            <span className="text-sm text-gray-600">Was this helpful?</span>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onFeedback(response.query_id, 5)}
            >
              <ThumbsUp className="w-4 h-4" />
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onFeedback(response.query_id, 1)}
            >
              <ThumbsDown className="w-4 h-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Context Panel */}
      <ContextPanel response={response} />
    </div>
  );
}

function QualityBadge({ label, value }: { label: string; value: number }) {
  const percentage = Math.round(value * 100);
  const variant = value >= 0.8 ? 'default' : value >= 0.6 ? 'secondary' : 'destructive';

  return (
    <Badge variant={variant} className="gap-1">
      {value >= 0.8 && <CheckCircle className="w-3 h-3" />}
      {label}: {percentage}%
    </Badge>
  );
}

function ContextPanel({ response }: { response: QueryResponse }) {
  const statutes = response.context.filter(doc => doc.doc_type === 'statute');
  const interpretiveCases = response.context.filter(doc => doc.is_interpretive);
  const otherCases = response.context.filter(doc => doc.doc_type === 'case' && !doc.is_interpretive);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <FileText className="w-5 h-5" />
          Sources & Context
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="statutes">
          <TabsList className="w-full">
            <TabsTrigger value="statutes" className="flex-1">
              Statutes ({statutes.length})
            </TabsTrigger>
            <TabsTrigger value="interpretive" className="flex-1">
              Interpretive Cases ({interpretiveCases.length})
            </TabsTrigger>
            <TabsTrigger value="cases" className="flex-1">
              Other Cases ({otherCases.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="statutes" className="space-y-2">
            {statutes.map(doc => (
              <DocumentCard key={doc.doc_id} doc={doc} />
            ))}
          </TabsContent>

          <TabsContent value="interpretive" className="space-y-2">
            {interpretiveCases.map(doc => (
              <DocumentCard key={doc.doc_id} doc={doc} showInterpretation />
            ))}
          </TabsContent>

          <TabsContent value="cases" className="space-y-2">
            {otherCases.map(doc => (
              <DocumentCard key={doc.doc_id} doc={doc} />
            ))}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

function DocumentCard({ doc, showInterpretation }: { doc: ContextDocument; showInterpretation?: boolean }) {
  return (
    <div className="p-3 bg-gray-50 rounded border border-gray-200">
      <div className="flex items-start justify-between mb-2">
        <div>
          <p className="font-medium text-sm">{doc.citation}</p>
          <p className="text-xs text-gray-600">{doc.title}</p>
        </div>
        <Badge variant="outline" className="text-xs">
          {(doc.score * 100).toFixed(0)}% match
        </Badge>
      </div>
      {showInterpretation && doc.interpretation_type && (
        <div className="flex gap-2 mb-2">
          <Badge variant="secondary" className="text-xs">
            {doc.interpretation_type}
          </Badge>
          {doc.interprets_statute_id && (
            <Badge variant="outline" className="text-xs">
              Interprets {doc.interprets_statute_id}
            </Badge>
          )}
        </div>
      )}
      <p className="text-sm text-gray-700 line-clamp-3">{doc.text}</p>
    </div>
  );
}
