"use client"

import type React from "react"

import { useEffect, useState } from "react"
import { Send, User, Bot, AlertCircle } from "lucide-react"
import { CopilotChat } from "@copilotkit/react-ui"

interface Message {
  id: string
  type: "user" | "assistant"
  content: string
  timestamp: Date
}

interface PromptPanelProps {
  onSubmit: (prompt: string) => void
  availableCash: number
}

const samplePrompts = [
  "Invest $50,000 in Apple and Nvidia equally",
  "Put $25,000 into Tesla and Microsoft",
  "Allocate $100,000 between Amazon and Google",
  "Invest $75,000 in Meta and Netflix",
]

export function PromptPanel({ onSubmit, availableCash }: PromptPanelProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      type: "assistant",
      content:
        "Hi! I'm your AI portfolio analyst. Tell me how much you'd like to invest and in which stocks, and I'll generate a comprehensive analysis for you.",
      timestamp: new Date(),
    },
  ])

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }



  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="p-4 border-b border-[#D8D8E5] bg-[#FAFCFA]">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xl">🪁</span>
          <div>
            <h1 className="text-lg font-semibold text-[#030507] font-['Roobert']">Portfolio Chat</h1>
            <div className="inline-block px-2 py-0.5 bg-[#BEC9FF] text-[#030507] text-xs font-semibold uppercase rounded">
              PRO
            </div>
          </div>
        </div>
        <p className="text-xs text-[#575758]">Chat with AI to create portfolio visualizations</p>

        {/* Available Cash Display */}
        <div className="mt-3 p-2 bg-[#86ECE4]/10 rounded-lg">
          <div className="text-xs text-[#575758] font-medium">Available Cash</div>
          <div className="text-sm font-semibold text-[#030507] font-['Roobert']">{formatCurrency(availableCash)}</div>
        </div>
      </div>

      {/* Messages */}
      {/* <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        {messages.map((message) => (
          <div key={message.id} className={`flex gap-3 ${message.type === "user" ? "flex-row-reverse" : ""}`}>
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${message.type === "user" ? "bg-[#030507] text-white" : "bg-[#86ECE4] text-[#030507]"
                }`}
            >
              {message.type === "user" ? <User size={14} /> : <Bot size={14} />}
            </div>
            <div className={`max-w-[80%] ${message.type === "user" ? "text-right" : ""}`}>
              <div
                className={`inline-block p-3 rounded-lg text-xs leading-relaxed ${message.type === "user"
                    ? "bg-[#030507] text-white rounded-br-sm"
                    : "bg-[#F0F0F4] text-[#030507] rounded-bl-sm"
                  }`}
              >
                {message.content}
              </div>
              <div className="text-xs text-[#858589] mt-1">
                {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </div>
            </div>
          </div>
        ))}
      </div> */}

      {/* Sample Prompts */}
      {/* {messages.length <= 1 && (
        <div className="px-4 pb-2">
          <div className="text-xs font-medium text-[#575758] mb-2">Try these examples:</div>
          <div className="flex flex-wrap gap-1">
            {samplePrompts.slice(0, 2).map((prompt, index) => (
              <button
                key={index}
                onClick={() => handleSampleClick(prompt)}
                className="text-xs bg-[#F0F0F4] hover:bg-[#E8E8EF] text-[#575758] px-2 py-1 rounded-md transition-colors"
              >
                {prompt.split(" ").slice(0, 4).join(" ")}...
              </button>
            ))}
          </div>
        </div>
      )} */}

      {/* Input */}
      {/* <div className="p-4 border-t border-[#D8D8E5] bg-[#FAFCFA]"> */}
      {/* Warning for insufficient funds */}
      {/* {wouldExceedCash && pendingInvestment > 0 && (
          <div className="mb-2 p-2 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
            <AlertCircle size={14} className="text-red-600" />
            <span className="text-xs text-red-600">
              Insufficient funds: Need {formatCurrency(pendingInvestment)}, have {formatCurrency(availableCash)}
            </span>
          </div>
        )}

      </div> */}
      <CopilotChat className="h-[78vh] p-2"
        Input={({ onSend }) => {
          const [input, setInput] = useState("")
          const extractInvestmentAmount = (prompt: string) => {
            const amountMatch = prompt.match(/\$?([\d,]+)k?/i)
            if (amountMatch) {
              const numStr = amountMatch[1].replace(/,/g, "")
              let amount = Number.parseInt(numStr)
              if (prompt.toLowerCase().includes("k")) {
                amount *= 1000
              }
              return amount
            }
            return 0
          }

          const handleSubmit = () => {
            if (!input.trim()) return

            const investmentAmount = extractInvestmentAmount(input)
            const hasInsufficientFunds = investmentAmount > availableCash

            const userMessage: Message = {
              id: Date.now().toString(),
              type: "user",
              content: input,
              timestamp: new Date(),
            }

            let assistantContent = ""
            if (hasInsufficientFunds) {
              assistantContent = `I notice you're trying to invest ${formatCurrency(investmentAmount)}, but you only have ${formatCurrency(availableCash)} available. Please adjust your investment amount or increase your total cash.`
            } else if (investmentAmount > 0) {
              assistantContent = `Perfect! I've allocated ${formatCurrency(investmentAmount)} to your portfolio analysis. Check out the visualization in the canvas!`
            } else {
              assistantContent = `I've generated your portfolio analysis. Please specify an investment amount (e.g., "$50,000") for more accurate calculations.`
            }

            const assistantMessage: Message = {
              id: (Date.now() + 1).toString(),
              type: "assistant",
              content: assistantContent,
              timestamp: new Date(),
            }

            setMessages((prev) => [...prev, userMessage, assistantMessage])

            if (!hasInsufficientFunds) {
              onSend(input)
            }
            setInput("")
          }

          const handleSampleClick = (prompt: string) => {
            setInput(prompt)
          }

          const handleKeyPress = (e: React.KeyboardEvent) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault()
              handleSubmit()
            }
          }

          const pendingInvestment = extractInvestmentAmount(input)
          const wouldExceedCash = pendingInvestment > availableCash
          return (
            <div className="p-4 border-t border-[#D8D8E5] bg-[#FAFCFA]">
              <div className="flex gap-2 w-full">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder="Your query comes here..."
                  className={`flex-1 px-3 py-2 border rounded-lg text-xs focus:outline-none focus:ring-2 focus:border-transparent placeholder-[#858589] text-black ${wouldExceedCash && pendingInvestment > 0
                    ? "border-red-300 focus:ring-red-200"
                    : "border-[#D8D8E5] focus:ring-[#BEC9FF]"
                    }`}
                />
                <button
                  onClick={handleSubmit}
                  disabled={!input.trim()}
                  className="w-10 h-10 bg-[#030507] text-white rounded-lg hover:bg-[#575758] disabled:bg-[#D8D8E5] disabled:text-[#858589] disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                >
                  <Send size={14} />
                </button>
              </div>
            </div>
          )
        }}
        UserMessage={({ message }) => {
          return (
            <div className={`flex gap-3 flex-row-reverse`}>
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-[#030507] text-white`}
              >
                <User size={14} />
              </div>
              <div className={`max-w-[80%] text-right`}>
                <div
                  className={`inline-block p-3 rounded-lg text-xs leading-relaxed bg-[#030507] text-white rounded-br-sm`}
                >
                  {message}
                </div>
                <div className="text-xs text-[#858589] mt-1">
                  {new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </div>
              </div>
            </div>
          )
        }}
        AssistantMessage={({ message, isLoading, subComponent }) => {
          useEffect(() => {
            console.log(message, "messagemessagemessagemessage")
          }, [message])
          return (
            <div className={`flex gap-3`}>
              {subComponent ? <div className="mt-2">{subComponent}</div> :
                <>
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-[#86ECE4] text-[#030507]`}
                  >
                    <Bot size={14} />
                  </div>
                  <div className={`max-w-[80%]`}>
                    <div
                      className={`inline-block p-3 rounded-lg text-xs leading-relaxed bg-[#F0F0F4] text-[#030507] rounded-bl-sm`}
                    >
                      {message}
                    </div>
                    <div className="text-xs text-[#858589] mt-1">
                      {new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </div>
                  </div>
                </>}
            </div>
          )
        }}
      // RenderResultMessage = {({message})=>{
      //   return (
      //     <div>
      //       {message.createdAt}
      //     </div>
      //   )
      // }}
      />

    </div >
  )
}
