"use client"

import { CopilotChat } from "@copilotkit/react-ui";
import { useEffect, useState } from "react";
import { useCopilotAction } from "@copilotkit/react-core";
import Table from "@/components/table";
export default function Home() {
  const [color, setColor] = useState("#000000");
  useCopilotAction({
    name: "render_table",
    description: "Render a tabular data with the given data. The data would be very generic",
    parameters: [
      {
        name : "columns",
        description : "The columns of the table that needs to be rendered",
        type : "string[]"
      },
      {
        name : "rows",
        description : "The rows of the table that needs to be rendered",
        type : "object[]",
        attributes : [
          {
            name : "row_data",
            description : "The data of the row that needs to be rendered",
            type : "string[]"
          }
        ]
      }
    ],
    renderAndWaitForResponse : ({args,respond}) => {
      console.log(args, "argsargs");
      useEffect(() => {
        if(respond){
          respond("the table with the given data has been rendered")
        }
      }, [args])
      // @ts-ignore
      return <Table size="sm" columns={args?.columns} rows={args?.rows} />
    },
    // handler: (args) => {
      // console.log(args, "argsargs");
    // }
  })


  return (
    <div className="min-h-screen bg-indigo-50 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-7xl grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Panel */}
        <div className="lg:col-span-2 flex flex-col gap-8">
          {/* Sales Performance by Region */}
          <div className="bg-white rounded-xl shadow p-6 border-t-4 border-indigo-500">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl font-semibold text-black">Q1 Sales Performance by Region</span>
            </div>
            <div className="text-xs text-gray-700 mb-4">Generated 12:55:24 pm</div>
            {/* Placeholder for Bar Chart */}
            <div className="h-64 flex items-end gap-6 justify-around">
              {/* Example bars */}
              {[
                { label: "North America", value: 2400000 },
                { label: "Europe", value: 1700000 },
                { label: "Asia Pacific", value: 3200000 },
                { label: "Latin America", value: 850000 },
                { label: "Middle East", value: 650000 },
              ].map((region, idx) => (
                <div key={region.label} className="flex flex-col items-center">
                  <div
                    className="bg-indigo-500 rounded-t w-12"
                    style={{ height: `${region.value / 40000}px`, backgroundColor: color }}
                  ></div>
                  <span className="text-xs mt-2 text-black text-center w-14">{region.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Key Performance Indicators */}
          <div className="bg-white rounded-xl shadow p-6 mt-2 border-t-4 border-indigo-500">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg font-semibold text-black">Key Performance Indicators</span>
            </div>
            <div className="text-xs text-gray-700 mb-4">Generated 12:57:24 pm</div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* KPI Cards */}
              <div className="bg-indigo-50 rounded-lg p-4 flex flex-col items-start border border-indigo-100">
                <span className="text-xs text-black mb-1 font-medium">Total Revenue</span>
                <span className="text-2xl font-bold text-black">$9.07M</span>
                <span className="text-xs text-green-600 font-semibold mt-1">+12.5%</span>
                <span className="text-xs text-gray-700 mt-2">Quarterly revenue growth</span>
              </div>
              <div className="bg-indigo-50 rounded-lg p-4 flex flex-col items-start border border-indigo-100">
                <span className="text-xs text-black mb-1 font-medium">Active Users</span>
                <span className="text-2xl font-bold text-black">847K</span>
                <span className="text-xs text-green-600 font-semibold mt-1">+8.2%</span>
                <span className="text-xs text-gray-700 mt-2">Monthly active users</span>
              </div>
              <div className="bg-indigo-50 rounded-lg p-4 flex flex-col items-start border border-indigo-100">
                <span className="text-xs text-black mb-1 font-medium">Conversion Rate</span>
                <span className="text-2xl font-bold text-black">3.4%</span>
                <span className="text-xs text-red-600 font-semibold mt-1">-0.3%</span>
                <span className="text-xs text-gray-700 mt-2">Lead to customer conversion</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel */}
        <div className="flex flex-col gap-6">
          <div className="bg-white rounded-xl shadow p-6 flex flex-col gap-4 h-[90vh] border-t-4 border-indigo-500 overflow-y-auto">
            <CopilotChat className="w-full h-full" />
          </div>
        </div>
      </div>
    </div>
  );
}
