"use client"

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

interface BarChartData {
  ticker: string
  return: number
}

interface BarChartComponentProps {
  data: BarChartData[]
}

export function BarChartComponent({ data }: BarChartComponentProps) {
  return (
    <div className="bg-white border border-[#D8D8E5] rounded-xl p-4">
      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E8E8EF" />
            <XAxis dataKey="ticker" stroke="#575758" fontSize={10} fontFamily="Plus Jakarta Sans" />
            <YAxis
              stroke="#575758"
              fontSize={10}
              fontFamily="Plus Jakarta Sans"
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "white",
                border: "1px solid #D8D8E5",
                borderRadius: "8px",
                fontSize: "11px",
                fontFamily: "Plus Jakarta Sans",
              }}
              formatter={(value: number) => [`${value.toFixed(1)}%`, "Return"]}
            />
            <Bar dataKey="return" fill="#86ECE4" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
