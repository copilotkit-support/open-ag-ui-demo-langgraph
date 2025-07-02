"use client"

import { CopilotChat } from "@copilotkit/react-ui";
import { useEffect, useState } from "react";
import { useCopilotAction } from "@copilotkit/react-core";
import Table from "@/components/table";
import CustomBarChart from "@/components/bar-chart";
export default function Home() {
  const [tableData, setTableData] = useState<{ columns: string[], rows: { row_data: (string | number)[] }[] }>({
    "columns": [
      "Company",
      "Ticker",
      "Current Price",
      "Revenue (2024)"
    ],
    "rows": [
      {
        "row_data": [
          "Apple Inc.",
          "AAPL",
          212.43,
          400366010368
        ]
      },
      {
        "row_data": [
          "Microsoft Corporation",
          "MSFT",
          491.85,
          270010007552
        ]
      },
      {
        "row_data": [
          "Alphabet Inc.",
          "GOOGL",
          176.71,
          359713013760
        ]
      },
      {
        "row_data": [
          "Amazon.com, Inc.",
          "AMZN",
          220.21,
          650313007104
        ]
      },
      {
        "row_data": [
          "Tesla, Inc.",
          "TSLA",
          312.77,
          95724003328
        ]
      },
    ]
  });
  const [tableTopic, setTableTopic] = useState<string>("Top 5 Stock Performers");
  const [barChartData, setBarChartData] = useState<{ x: string, y: number }[]>([
    {
      "x": "2024",
      "y": 637959
    },
    {
      "x": "2023",
      "y": 574785
    },
    {
      "x": "2022",
      "y": 513983
    },
    {
      "x": "2021",
      "y": 469822
    }
  ]);
  const [barChartTopic, setBarChartTopic] = useState<string>("Amazon Revenue (Last 4 Years)");

  useCopilotAction({
    name: "render_table",
    description: "Render a tabular data with the given data. The data would be very generic",
    parameters: [
      {
        name: "topic",
        description: "The topic of the table that needs to be rendered",
        type: "string"
      },
      {
        name: "columns",
        description: "The columns of the table that needs to be rendered",
        type: "string[]"
      },
      {
        name: "rows",
        description: "The rows of the table that needs to be rendered",
        type: "object[]",
        attributes: [
          {
            name: "row_data",
            description: "The data of the row that needs to be rendered",
            type: "string[]"
          }
        ]
      }
    ],
    renderAndWaitForResponse: ({ args, respond }) => {
      console.log(args, "argsargs");
      const [updated, setUpdated] = useState(false);
      return <>
        {/* @ts-ignore */}
        <Table size="sm" columns={args?.columns} rows={args?.rows} />
        <button hidden={updated} className="mt-2 mr-2 bg-indigo-500 text-white px-4 py-1 rounded-xl hover:bg-indigo-600 transition-all duration-300 cursor-pointer" onClick={() => {
          respond?.("the table with the given data has been rendered")
          setTableData({ columns: args?.columns || [], rows: args?.rows || [] })
          setUpdated(true)
          setTableTopic(args?.topic || "")
        }}>
          Approve
        </button>
        <button hidden={updated} className="mt-2 bg-red-500 text-white px-4 py-1 rounded-xl hover:bg-red-600 transition-all duration-300 cursor-pointer" onClick={() => {
          respond?.("the table with the given data has been rejected by the user.")
          setUpdated(true)
        }}>
          Reject
        </button>
      </>
    },
    // handler: (args) => {
    // console.log(args, "argsargs");
    // }
  })

  useCopilotAction({
    name: "render_bar_chart",
    description: "Render a bar chart with the given data. The data would be very generic",
    parameters: [
      {
        name: "topic",
        description: "The topic of the bar chart that needs to be rendered",
        type: "string"
      },
      {
        name: "data",
        description: "The data of the bar chart that needs to be rendered",
        type: "object[]",
        attributes: [
          {
            name: "x",
            description: "The x-axis of the bar chart that needs to be rendered. if individual string is long, make a clipped word of it. For example, if the string is 'United States of America', make it 'USA', if the string is 'Amazon Inc', make it 'AMZ', if its a long number like 100000000000, make it 100B",
            type: "string"
          },
          {
            name: "y",
            description: "The y-axis of the bar chart that needs to be rendered. if individual string is long, make a clipped word of it. For example, if the string is 'United States of America', make it 'USA', if the string is 'Amazon Inc', make it 'AMZ', if its a long number like 100000000000, make it 100B",
            type: "number"
          }
        ]
      }
    ],
    renderAndWaitForResponse: ({ args, respond }) => {
      console.log(args, "argsargs");
      const [updated, setUpdated] = useState(false);
      return <>
        {/* @ts-ignore */}
        <CustomBarChart data={args?.data} barLabel={args?.topic} />
        <button hidden={updated} className="mt-2 mr-2 bg-indigo-500 text-white px-4 py-1 rounded-xl hover:bg-indigo-600 transition-all duration-300 cursor-pointer" onClick={() => {
          respond?.("the table with the given data has been rendered")
          setUpdated(true)
          setBarChartData(args?.data || [])
          setBarChartTopic(args?.topic || "")
        }}>
          Approve
        </button>
        <button hidden={updated} className="mt-2 bg-red-500 text-white px-4 py-1 rounded-xl hover:bg-red-600 transition-all duration-300 cursor-pointer" onClick={() => {
          respond?.("the table with the given data has been rejected by the user.")
          setUpdated(true)
        }}>
          Reject
        </button>
      </>
    }
  })


  return (
    <div className="min-h-screen bg-indigo-50 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-7xl grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Panel */}
        <div className="lg:col-span-2 flex flex-col gap-8 h-[90vh] overflow-y-auto">


          {/* {Bar Chart data} */}
          {barChartTopic && <div className="bg-white rounded-xl shadow p-6 border-t-4 border-indigo-500">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl font-semibold text-black">{barChartTopic}</span>
            </div>
            <div className="text-xs text-gray-700 mb-4">Generated {new Date().toLocaleTimeString()}</div>
            {barChartData.length > 0 && <CustomBarChart data={barChartData} xKey={"x"} barKey={"y"} barLabel={barChartTopic} />}
          </div>}
          
          {/* {Table data} */}
          {tableTopic && <div className="bg-white rounded-xl shadow p-6 border-t-4 border-indigo-500">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl font-semibold text-black">{tableTopic}</span>
            </div>
            <div className="text-xs text-gray-700 mb-4">Generated {new Date().toLocaleTimeString()}</div>
            {tableData.columns.length > 0 && tableData.rows.length > 0 && <Table size="lg" className="bg-white" columns={tableData.columns} rows={tableData.rows} />}
          </div>}



          {/* Key Performance Indicators */}
          {/* <div className="bg-white rounded-xl shadow p-6 mt-2 border-t-4 border-indigo-500">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg font-semibold text-black">Key Performance Indicators</span>
            </div>
            <div className="text-xs text-gray-700 mb-4">Generated 12:57:24 pm</div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
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
          </div> */}
        </div>

        {/* Right Panel */}
        <div className="flex flex-col gap-6">
          <div className="bg-white rounded-xl shadow p-6 flex flex-col gap-4 h-[90vh] border-t-4 border-indigo-500 overflow-y-auto">
            <CopilotChat 
            labels={{
              initial : "Hi, I am a stock agent. I can help you analyze and compare different stocks. Please ask me anything about the stock market.",
            }}
            className="w-full h-full" />
          </div>
        </div>
      </div>
    </div>
  );
}
