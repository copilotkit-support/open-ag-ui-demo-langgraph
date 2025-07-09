"use client"

import { useState } from "react"
import { PromptPanel } from "./components/prompt-panel"
import { GenerativeCanvas } from "./components/generative-canvas"
import { ComponentTree } from "./components/component-tree"
import { CashPanel } from "./components/cash-panel"
import { mockPortfolioStates } from "./lib/mock-data"
import { useCopilotAction } from "@copilotkit/react-core"

export default function OpenStocksCanvas() {
  const [currentPrompt, setCurrentPrompt] = useState("")
  const [currentState, setCurrentState] = useState(mockPortfolioStates[0])
  const [showComponentTree, setShowComponentTree] = useState(false)
  const [totalCash, setTotalCash] = useState(1000000)
  const [investedAmount, setInvestedAmount] = useState(0)

  const handlePromptSubmit = (prompt: string) => {
    setCurrentPrompt(prompt)

    // Extract investment amount from prompt
    const amountMatch = prompt.match(/\$?([\d,]+)k?/i)
    let amount = 0
    if (amountMatch) {
      const numStr = amountMatch[1].replace(/,/g, "")
      amount = Number.parseInt(numStr)
      if (prompt.toLowerCase().includes("k")) {
        amount *= 1000
      }
    }

    // Simulate AI response by matching prompt to mock states
    const matchedState =
      mockPortfolioStates.find((state) => prompt.toLowerCase().includes(state.trigger.toLowerCase())) ||
      mockPortfolioStates[0]

    // Calculate current portfolio value based on performance
    const latestPerformance = matchedState.performanceData[matchedState.performanceData.length - 1]
    const initialInvestment = matchedState.performanceData[0].portfolio
    const performanceMultiplier = latestPerformance.portfolio / initialInvestment
    const currentPortfolioValue = amount * performanceMultiplier

    // Update the matched state with the extracted amount
    const updatedState = {
      ...matchedState,
      investmentAmount: amount,
      currentPortfolioValue: currentPortfolioValue,
      allocations: matchedState.allocations.map((allocation) => ({
        ...allocation,
        currentValue: (currentPortfolioValue * allocation.allocation) / 100,
      })),
    }

    setCurrentState(updatedState)
    setInvestedAmount(amount)
  }

  const toggleComponentTree = () => {
    setShowComponentTree(!showComponentTree)
  }

  const availableCash = totalCash - investedAmount
  const currentPortfolioValue = currentState.currentPortfolioValue || investedAmount


  useCopilotAction({
    name : "changeBackgroundColor",
    parameters : [
      {
        name : "color",
        type : "string",
        description : "The color to change the background to",
        required : true
      }
    ],
    description : "This is an action to change the background color of the canvas",
    render : ({args})=>{
      console.log(args.color, "args")
      return (
        <div>
          <h1>{args.color}</h1>
        </div>
      )
    }
  })

  


  return (
    <div className="h-screen bg-[#FAFCFA] flex overflow-hidden">
      {/* Left Panel - Prompt Input */}
      <div className="w-72 border-r border-[#D8D8E5] bg-white flex-shrink-0">
        <PromptPanel onSubmit={handlePromptSubmit} availableCash={availableCash} />
      </div>

      {/* Center Panel - Generative Canvas */}
      <div className="flex-1 relative min-w-0">
        {/* Top Bar with Cash Info */}
        <div className="absolute top-0 left-0 right-0 bg-white border-b border-[#D8D8E5] p-4 z-10">
          <CashPanel
            totalCash={totalCash}
            investedAmount={investedAmount}
            currentPortfolioValue={currentPortfolioValue}
            onTotalCashChange={setTotalCash}
          />
        </div>

        <div className="absolute top-4 right-4 z-20">
          <button
            onClick={toggleComponentTree}
            className="px-3 py-1 text-xs font-semibold text-[#575758] bg-white border border-[#D8D8E5] rounded-md hover:bg-[#F0F0F4] transition-colors"
          >
            {showComponentTree ? "Hide Tree" : "Show Tree"}
          </button>
        </div>

        <div className="pt-20 h-full">
          <GenerativeCanvas portfolioState={currentState} />
        </div>
      </div>

      {/* Right Panel - Component Tree (Optional) */}
      {showComponentTree && (
        <div className="w-64 border-l border-[#D8D8E5] bg-white flex-shrink-0">
          <ComponentTree portfolioState={currentState} />
        </div>
      )}
    </div>
  )
}
