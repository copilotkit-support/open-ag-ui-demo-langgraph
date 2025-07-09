"use client"

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"

interface LineChartData {
  date: string
  portfolio: number
  spy: number
}

interface LineChartComponentProps {
  data: LineChartData[]
}

export function LineChartComponent({ data }: LineChartComponentProps) {
  return (
    <div className="bg-white border border-[#D8D8E5] rounded-xl p-4">
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E8E8EF" />
            <XAxis dataKey="date" stroke="#575758" fontSize={10} fontFamily="Plus Jakarta Sans" />
            <YAxis
              stroke="#575758"
              fontSize={10}
              fontFamily="Plus Jakarta Sans"
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "white",
                border: "1px solid #D8D8E5",
                borderRadius: "8px",
                fontSize: "11px",
                fontFamily: "Plus Jakarta Sans",
              }}
              formatter={(value: number, name: string) => [
                `$${value.toLocaleString()}`,
                name === "portfolio" ? "Portfolio" : "SPY",
              ]}
            />
            <Legend
              wrapperStyle={{
                fontSize: "11px",
                fontFamily: "Plus Jakarta Sans",
                fontWeight: 500,
              }}
            />
            <Line type="monotone" dataKey="portfolio" stroke="#86ECE4" strokeWidth={2} name="Portfolio" dot={false} />
            <Line type="monotone" dataKey="spy" stroke="#BEC9FF" strokeWidth={2} name="SPY" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
