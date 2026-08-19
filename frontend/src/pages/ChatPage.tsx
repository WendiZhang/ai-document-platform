import { useEffect, useRef, useState } from "react";
import {
  Bot,
  FileText,
  LoaderCircle,
  MessageSquarePlus,
  RefreshCw,
  Send,
  Sparkles,
  Trash2,
  User,
} from "lucide-react";
import {
  Link,
} from "react-router";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  createChatSession,
  deleteChatSession,
  getChatMessages,
  getChatSessions,
  streamChat,
} from "../api/chat";
import { useDocuments } from "../hooks/useDocuments";
import type {
  ChatMessage,
  ChatSource,
} from "../types/chat";

export default function ChatPage() {
  const queryClient = useQueryClient();

  const [question, setQuestion] = useState("");
  const [selectedSessionId, setSelectedSessionId] =
    useState<string | null>(null);
  const [selectedDocumentId, setSelectedDocumentId] =
    useState("all");

  const [isStreaming, setIsStreaming] =
    useState(false);

  const [streamingAnswer, setStreamingAnswer] =
    useState("");

  const [streamingSources, setStreamingSources] =
    useState<ChatSource[]>([]);

  const [streamingError, setStreamingError] =
    useState("");

  const {
    data: sessions = [],
    isLoading: sessionsLoading,
    isError: sessionsError,
  } = useQuery({
    queryKey: ["chat-sessions"],
    queryFn: getChatSessions,
  });

  const {
    data: messages = [],
    isLoading: messagesLoading,
    isError: messagesError,
  } = useQuery({
    queryKey: [
      "chat-messages",
      selectedSessionId,
    ],
    queryFn: () =>
      getChatMessages(selectedSessionId!),
    enabled: Boolean(selectedSessionId),
  });

  const {
    data: documents = [],
  } = useDocuments();

  const messagesEndRef =
    useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (
      !selectedSessionId &&
      sessions.length > 0
    ) {
      setSelectedSessionId(
        sessions[0].id,
      );
    }
  }, [
    selectedSessionId,
    sessions,
  ]);

  useEffect(() => {
    // Only follow the conversation while an answer is streaming. Keeping
    // this disabled for ordinary query updates prevents deleting a chat or
    // switching sessions from unexpectedly jumping the page to the bottom.
    if (!isStreaming) {
      return;
    }

    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [
    messages,
    streamingAnswer,
    isStreaming,
  ]);

  const createSessionMutation = useMutation({
    mutationFn: createChatSession,

    onSuccess: async (session) => {
      await queryClient.invalidateQueries({
        queryKey: ["chat-sessions"],
      });

      setSelectedSessionId(session.id);
      setQuestion("");
    },
  });

  const deleteSessionMutation = useMutation({
    mutationFn: deleteChatSession,

    onSuccess: async (_, deletedSessionId) => {
      queryClient.removeQueries({
        queryKey: [
          "chat-messages",
          deletedSessionId,
        ],
      });

      setSelectedSessionId(null);

      await queryClient.invalidateQueries({
        queryKey: ["chat-sessions"],
      });
    },
  });

  function handleNewChat() {
    createSessionMutation.mutate();
  }

  function handleRefresh() {
    if (isStreaming) {
      return;
    }

    void Promise.all([
      queryClient.invalidateQueries({
        queryKey: ["chat-sessions"],
      }),
      selectedSessionId
        ? queryClient.invalidateQueries({
            queryKey: [
              "chat-messages",
              selectedSessionId,
            ],
          })
        : Promise.resolve(),
      queryClient.invalidateQueries({
        queryKey: ["documents"],
      }),
    ]);
  }

  function handleDeleteSession(
    sessionId: string,
    title: string,
  ) {
    const confirmed = window.confirm(
      `Delete "${title}"?`,
    );

    if (!confirmed) {
      return;
    }

    deleteSessionMutation.mutate(
      sessionId,
    );
  }

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const cleanedQuestion =
      question.trim();

    if (
      !cleanedQuestion ||
      !selectedSessionId ||
      isStreaming
    ) {
      return;
    }

    setIsStreaming(true);
    setStreamingAnswer("");
    setStreamingSources([]);
    setStreamingError("");
    setQuestion("");

    try {
      await streamChat(
        selectedSessionId,
        {
          question: cleanedQuestion,
          document_id:
            selectedDocumentId === "all"
              ? null
              : selectedDocumentId,
        },
        (event) => {
          if (event.type === "delta") {
            setStreamingAnswer(
              (current) =>
                current + event.content,
            );
          }

          if (event.type === "sources") {
            setStreamingSources(
              event.sources,
            );
          }

          if (event.type === "error") {
            setStreamingError(
              event.message,
            );
          }
        },
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: [
            "chat-messages",
            selectedSessionId,
          ],
        }),

        queryClient.invalidateQueries({
          queryKey: ["chat-sessions"],
        }),
      ]);
    } catch (error) {
      setStreamingError(
        error instanceof Error
          ? error.message
          : "The AI response could not be generated.",
      );
    } finally {
      setIsStreaming(false);
      setStreamingAnswer("");
      setStreamingSources([]);
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-[1500px] flex-col px-6 py-10">
      <div>
        <p className="flex items-center gap-2 text-sm font-medium text-blue-600">
          <Sparkles size={17} />
          AI Document Assistant
        </p>

        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">
          Ask your documents
        </h1>

        <p className="mt-2 max-w-2xl text-slate-600">
          Ask questions, revisit previous conversations,
          and receive answers grounded in your documents.
        </p>
      </div>

      <div className="mt-8 grid min-h-[680px] flex-1 overflow-hidden rounded-2xl border border-slate-200 bg-white lg:grid-cols-[300px_minmax(0,1fr)]">
        <aside className="border-b border-slate-200 bg-slate-50 lg:border-b-0 lg:border-r">
          <div className="border-b border-slate-200 p-4">
            <button
              type="button"
              onClick={handleNewChat}
              disabled={
                createSessionMutation.isPending ||
                isStreaming
              }
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 !text-white px-4 py-3 text-sm font-semibold shadow-sm shadow-blue-200 transition hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {createSessionMutation.isPending ? (
                <LoaderCircle
                  size={17}
                  className="animate-spin"
                />
              ) : (
                <MessageSquarePlus
                  size={17}
                />
              )}

              New chat
            </button>
          </div>

          <div className="max-h-72 overflow-y-auto p-3 lg:max-h-[610px]">
            {sessionsLoading && (
              <div className="flex items-center justify-center gap-2 py-8 text-sm text-slate-500">
                <LoaderCircle
                  size={17}
                  className="animate-spin"
                />
                Loading chats...
              </div>
            )}

            {sessionsError && (
              <p className="rounded-xl bg-red-50 px-3 py-4 text-sm text-red-700">
                Chat sessions could not be loaded.
              </p>
            )}

            {!sessionsLoading &&
              !sessionsError &&
              sessions.length === 0 && (
                <div className="px-3 py-8 text-center">
                  <Bot
                    size={28}
                    className="mx-auto text-slate-300"
                  />

                  <p className="mt-3 text-sm font-medium text-slate-700">
                    No conversations yet
                  </p>

                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    Create a new chat to begin.
                  </p>
                </div>
              )}

            <div className="space-y-2">
              {sessions.map((session) => {
                const isSelected =
                  selectedSessionId ===
                  session.id;

                return (
                  <div
                    key={session.id}
                    className={[
                      "group flex items-start gap-2 rounded-xl border p-2 transition",
                      isSelected
                        ? "border-slate-300 bg-white shadow-sm"
                        : "border-transparent hover:bg-white",
                    ].join(" ")}
                  >
                    <button
                      type="button"
                      onClick={() => {
                        if (!isStreaming) {
                          setSelectedSessionId(
                            session.id,
                          );
                        }
                      }}
                      className="min-w-0 flex-1 px-2 py-1 text-left"
                    >
                      <p className="truncate text-sm font-medium text-slate-800">
                        {session.title}
                      </p>

                      <p className="mt-1 text-xs text-slate-400">
                        {new Date(
                          session.updated_at,
                        ).toLocaleDateString()}
                      </p>
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        handleDeleteSession(
                          session.id,
                          session.title,
                        )
                      }
                      disabled={
                        deleteSessionMutation.isPending ||
                        isStreaming
                      }
                      aria-label={`Delete ${session.title}`}
                      className="rounded-lg p-2 text-slate-400 opacity-0 transition hover:bg-red-50 hover:text-red-600 group-hover:opacity-100 disabled:opacity-30"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </aside>

        <section className="flex min-h-[620px] min-w-0 flex-col">
          <div className="border-b border-slate-200 px-5 py-4">
            <div className="mb-2 flex items-center justify-between gap-3">
              <label
                htmlFor="document-filter"
                className="block text-xs font-semibold uppercase tracking-wide text-slate-500"
              >
                Search scope
              </label>

              <button
                type="button"
                onClick={handleRefresh}
                disabled={isStreaming}
                aria-label="Refresh chat"
                title="Refresh chat"
                className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <RefreshCw size={16} />
              </button>
            </div>

            <select
              id="document-filter"
              value={selectedDocumentId}
              disabled={isStreaming}
              onChange={(event) =>
                setSelectedDocumentId(
                  event.target.value,
                )
              }
              className="w-full max-w-sm rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-700 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:cursor-not-allowed disabled:bg-slate-100"
            >
              <option value="all">
                All embedded documents
              </option>

              {documents
                .filter(
                  (document) =>
                    document.status === "ready" ||
                    document.status ===
                    "embedded",
                )
                .map((document) => (
                  <option
                    key={document.id}
                    value={document.id}
                  >
                    {
                      document.original_filename
                    }
                  </option>
                ))}
            </select>
          </div>

          <div className="flex-1 overflow-y-auto p-6">
            {!selectedSessionId && (
              <EmptyConversation
                onCreateChat={handleNewChat}
                isCreating={
                  createSessionMutation.isPending
                }
              />
            )}

            {selectedSessionId &&
              messagesLoading && (
                <div className="flex h-full min-h-[420px] items-center justify-center gap-2 text-slate-500">
                  <LoaderCircle
                    size={20}
                    className="animate-spin"
                  />
                  Loading conversation...
                </div>
              )}

            {selectedSessionId &&
              messagesError && (
                <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
                  The conversation could not be loaded.
                </div>
              )}

            {selectedSessionId &&
              !messagesLoading &&
              !messagesError &&
              messages.length === 0 && (
                <div className="flex h-full min-h-[420px] items-center justify-center">
                  <div className="max-w-lg text-center">
                    <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
                      <Bot size={26} />
                    </div>

                    <h2 className="mt-5 text-lg font-semibold text-slate-900">
                      Ask your first question
                    </h2>

                    <p className="mt-2 text-sm leading-6 text-slate-500">
                      For example: “What technologies are
                      mentioned?” or “Summarize the main
                      points in this document.”
                    </p>
                  </div>
                </div>
              )}

            <div className="space-y-6">
              {messages.map((message) => (
                <ChatMessageItem
                  key={message.id}
                  message={message}
                />
              ))}

              {isStreaming && (
                <div className="flex gap-3">
                  <AssistantAvatar />

                  <div className="max-w-3xl">
                    <div className="whitespace-pre-wrap rounded-2xl bg-slate-100 px-4 py-3 text-sm leading-7 text-slate-700">
                      {streamingAnswer || (
                        <span className="flex items-center gap-2 text-slate-500">
                          <LoaderCircle
                            size={17}
                            className="animate-spin"
                          />
                          Thinking...
                        </span>
                      )}
                    </div>

                    {streamingSources.length > 0 && (
                      <Sources
                        sources={streamingSources}
                      />
                    )}
                  </div>
                </div>
              )}

              {streamingError && (
                <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
                  {streamingError}
                </div>
              )}
            </div>
          </div>

          <form
            onSubmit={handleSubmit}
            className="border-t border-slate-200 p-4"
          >
            <div className="flex items-end gap-3 rounded-2xl border border-slate-300 bg-white p-3 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-100">
              <textarea
                value={question}
                onChange={(event) =>
                  setQuestion(
                    event.target.value,
                  )
                }
                onKeyDown={(event) => {
                  if (
                    event.key === "Enter" &&
                    !event.shiftKey
                  ) {
                    event.preventDefault();

                    event.currentTarget
                      .closest("form")
                      ?.requestSubmit();
                  }
                }}
                placeholder={
                  selectedSessionId
                    ? "Ask a question about your documents..."
                    : "Create a chat before asking a question..."
                }
                rows={2}
                disabled={
                  !selectedSessionId ||
                  isStreaming
                }
                className="max-h-40 min-h-12 flex-1 resize-none border-0 bg-transparent px-2 py-2 text-sm text-slate-900 outline-none placeholder:text-slate-400 disabled:cursor-not-allowed disabled:bg-slate-50"
              />

              <button
                type="submit"
                disabled={
                  !selectedSessionId ||
                  !question.trim() ||
                  isStreaming
                }
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-600 !text-white shadow-sm shadow-blue-200 transition hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-100 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <Send size={17} />
              </button>
            </div>
          </form>
        </section>


        {isStreaming && (
          <div className="flex gap-3">
            <AssistantAvatar />

            <div className="max-w-3xl">
              <div className="whitespace-pre-wrap rounded-2xl bg-slate-100 px-4 py-3 text-sm leading-7 text-slate-700">
                {streamingAnswer || (
                  <span className="flex items-center gap-2 text-slate-500">
                    <LoaderCircle
                      size={17}
                      className="animate-spin"
                    />
                    Thinking...
                  </span>
                )}
              </div>

              {streamingSources.length > 0 && (
                <Sources
                  sources={streamingSources}
                />
              )}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />

      </div>
    </div>
  );
}

type EmptyConversationProps = {
  onCreateChat: () => void;
  isCreating: boolean;
};

function EmptyConversation({
  onCreateChat,
  isCreating,
}: EmptyConversationProps) {
  return (
    <div className="flex h-full min-h-[420px] items-center justify-center">
      <div className="max-w-md text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
          <MessageSquarePlus size={25} />
        </div>

        <h2 className="mt-5 text-lg font-semibold text-slate-900">
          Start a conversation
        </h2>

        <p className="mt-2 text-sm leading-6 text-slate-500">
          Create a chat session, then ask questions
          grounded in your embedded documents.
        </p>

        <button
          type="button"
          onClick={onCreateChat}
          disabled={isCreating}
          className="mt-5 inline-flex items-center gap-2 rounded-xl bg-blue-600 !text-white px-4 py-3 text-sm font-semibold shadow-sm shadow-blue-200 hover:bg-blue-700 disabled:opacity-50"
        >
          {isCreating ? (
            <LoaderCircle
              size={17}
              className="animate-spin"
            />
          ) : (
            <MessageSquarePlus
              size={17}
            />
          )}

          Create new chat
        </button>
      </div>
    </div>
  );
}

type ChatMessageItemProps = {
  message: ChatMessage;
};

function ChatMessageItem({
  message,
}: ChatMessageItemProps) {
  const isUser =
    message.role === "user";

  return (
    <div
      className={
        isUser
          ? "flex justify-end gap-3"
          : "flex gap-3"
      }
    >
      {!isUser && <AssistantAvatar />}

      <div
        className={
          isUser
            ? "max-w-2xl rounded-2xl bg-slate-900 px-4 py-3 text-sm leading-7 text-white"
            : "max-w-3xl"
        }
      >
        {!isUser && (
          <div className="whitespace-pre-wrap rounded-2xl bg-slate-100 px-4 py-3 text-sm leading-7 text-slate-700">
            {message.content}
          </div>
        )}

        {isUser && (
          <p className="whitespace-pre-wrap">
            {message.content}
          </p>
        )}

        {!isUser &&
          message.sources &&
          message.sources.length > 0 && (
            <Sources
              sources={message.sources}
            />
          )}
      </div>

      {isUser && (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-200 text-slate-700">
          <User size={18} />
        </div>
      )}
    </div>
  );
}

function AssistantAvatar() {
  return (
    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-50 text-blue-600">
      <Bot size={18} />
    </div>
  );
}

type SourcesProps = {
  sources: ChatSource[];
};

function Sources({
  sources,
}: SourcesProps) {
  return (
    <div className="mt-3 rounded-2xl border border-slate-200 bg-white p-4">
      <div className="flex items-center gap-2">
        <FileText
          size={16}
          className="text-slate-500"
        />

        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Sources
        </p>
      </div>

      <div className="mt-3 space-y-3">
        {sources.map((source) => (
          <details
            key={source.chunk_id}
            className="rounded-xl border border-slate-200"
          >
            <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-slate-700">
              <Link
                to={`/documents/${source.document_id}`}
                className="text-blue-600 hover:text-blue-700"
              >
                {source.document_name}
              </Link>

              {" · "}
              Chunk {source.chunk_index + 1}
              {" · "}
              {(source.score * 100).toFixed(0)}%
              match
            </summary>

            <p className="whitespace-pre-wrap border-t border-slate-200 px-4 py-3 text-sm leading-6 text-slate-600">
              {source.content}
            </p>
          </details>
        ))}
      </div>
    </div>
  );
}
