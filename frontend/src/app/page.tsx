"use client"

import { CopilotChat, useCopilotChatSuggestions } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import { Role, TextMessage } from "@copilotkit/runtime-client-gql";
import { useEffect, useState } from "react";
import { useCoAgentStateRender, useCopilotAction, useCopilotChat } from "@copilotkit/react-core";
import Table from "@/components/table";
import CustomBarChart from "@/components/bar-chart";
import { initialMessage, suggestions } from "@/utils/prompts";
import ToolLog from "@/components/tool-log";
import DotLoader from "@/components/dot-loader";
import CustomLineChart from "@/components/line-chart";

interface TableData {
  topic: string;
  type: "table";
  columns: string[];
  rows: { row_data: (string | number)[] }[];
  date: string;
}

interface BarChartData {
  topic: string;
  type: "barChart";
  date: string;
  data: { x: string, y: number }[];
}

interface LineChartData {
  topic: string;
  type: "lineChart";
  date: string;
  xArr: string[];
  items: any[];
}

export default function Home() {
  const [data, setData] = useState<(BarChartData | TableData | LineChartData)[] | []>([]);
  const { visibleMessages, appendMessage } = useCopilotChat()

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
    renderAndWaitForResponse: ({ args, respond, status }) => {
      console.log(status, "barargs");
      const [updated, setUpdated] = useState(false);
      return <>
        {/* @ts-ignore */}
        <CustomBarChart data={args?.data} barLabel={args?.topic} />
        <button hidden={updated} className="mt-2 mr-2 bg-indigo-500 text-white px-4 py-1 rounded-xl hover:bg-indigo-600 transition-all duration-300 cursor-pointer" onClick={() => {

          respond?.("accepted")
          setUpdated(true)

          setData([...data, { type: "barChart", topic: args?.topic || "", date: new Date().toLocaleTimeString(), data: args?.data || [] }])
        }}>
          Approve
        </button>
        <button hidden={updated} className="mt-2 bg-red-500 text-white px-4 py-1 rounded-xl hover:bg-red-600 transition-all duration-300 cursor-pointer" onClick={() => {
          respond?.("rejected")
          setUpdated(true)
        }}>
          Reject
        </button>
        {(status === "inProgress" || status === "executing") && <DotLoader />}
      </>
    }
  })
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
    renderAndWaitForResponse: ({ args, respond, status }) => {
      console.log(status, "tabsargs");
      const [updated, setUpdated] = useState(false);
      return <>
        {/* @ts-ignore */}
        <Table size="sm" columns={args?.columns} rows={args?.rows} />
        <button hidden={updated} className="mt-2 mr-2 bg-indigo-500 text-white px-4 py-1 rounded-xl hover:bg-indigo-600 transition-all duration-300 cursor-pointer" onClick={() => {

          respond?.("accepted")
          setData([...data, { type: "table", topic: args?.topic || "", columns: args?.columns || [], rows: args?.rows || [], date: new Date().toLocaleTimeString() }])
          setUpdated(true)
        }}>
          Approve
        </button>
        <button hidden={updated} className="mt-2 bg-red-500 text-white px-4 py-1 rounded-xl hover:bg-red-600 transition-all duration-300 cursor-pointer" onClick={() => {
          respond?.("rejected")
          setUpdated(true)
        }}>
          Reject
        </button>
        {(status === "inProgress" || status === "executing") && <DotLoader />}
      </>
    },
  })
  useCopilotAction({
    name: "render_line_chart",
    description: `Render a Line-chart based on the given data. Example input format: [[{"name": "2021", "value": 566,accessorKey : "APPL"}, {"name": "2022", "value": 20,accessorKey : "APPL"}, {"name": "2023", "value": 30,accessorKey : "APPL"}],[{"name": "2021", "value": 10,accessorKey : "GOOG"}, {"name": "2022", "value": 20,accessorKey : "GOOG"}, {"name": "2023", "value": 30,accessorKey : "GOOG"}]]. If dates are present convert them to the format "YYYY". Also if name length is long, provide short name for the item in the input. For example, If the name is Jon.snow@got.com, then the short name is Jon`,
    parameters: [
      {
        name: "items",
        type: "object[]",
        description: "The data to be displayed in the line chart",
        required: true,
        items: {
          type: "object",
          attributes: [
            {
              name: "name",
              type: "string",
              description: "The name of the item or stock",
              required: true
            },
            {
              name: "value",
              type: "number",
              description: "The value of the item or stock",
              required: true
            },
            {
              name: "accessorKey",
              type: "string",
              description: "The accessor key of the item. It can be the author name or the repository name or the branch name or the status name or the date just value.",
              required: true
            }
          ]
        }
      },
      {
        name: "topic",
        type: "string",
        description: "The topic of the line chart that needs to be rendered",
        required: true
      }
    ],
    renderAndWaitForResponse: ({ args, respond, status }: any) => {
      console.log(args, "lineargs");
      const [updated, setUpdated] = useState(false);
      const [xarr, setXarr] = useState<string[]>([])
      const [chartData, setChartData] = useState<any[]>([])
      useEffect(() => {
        setXarr(args?.items?.map((item: any) => item[0]?.accessorKey));
        const chartVals = [];
        const numMonths = args?.items[0]?.length || 0;
        const numStocks = args?.items.length;

        for (let i = 0; i < numMonths; i++) {
          const entry: any = {};
          for (let j = 0; j < numStocks; j++) {
            const stock = args?.items[j][i];
            entry[stock.accessorKey] = stock.value;
            entry.name = stock.name;
          }
          chartVals.push(entry);
        }
        console.log(chartVals, "chartVals")
        setChartData(chartVals);
      }, [args?.items])
      return <>
        <CustomLineChart data={chartData} xarr={xarr} />
        <button hidden={updated} className="mt-2 mr-2 bg-indigo-500 text-white px-4 py-1 rounded-xl hover:bg-indigo-600 transition-all duration-300 cursor-pointer" onClick={() => {

          respond?.("accepted")
          setData([...data, { type: "lineChart", topic: args?.topic || "", items: chartData || [], date: new Date().toLocaleTimeString(), xArr: xarr }])
          setUpdated(true)
        }}>
          Approve
        </button>
        <button hidden={updated} className="mt-2 bg-red-500 text-white px-4 py-1 rounded-xl hover:bg-red-600 transition-all duration-300 cursor-pointer" onClick={() => {
          respond?.("rejected")
          setUpdated(true)
        }}>
          Reject
        </button>
        {(status === "inProgress" || status === "executing") && <DotLoader />}
      </>

    }
  })

  useCoAgentStateRender({
    name: "langgraphAgent",
    render: ({ state, status, nodeName }) => {
      // console.log(state, status, nodeName, "state");
      return (state.items.length > 0 ? <ToolLog state={state.items} /> : status === "inProgress" ? <DotLoader /> : <></>)
    }
  })


  useCopilotChatSuggestions({
    instructions: suggestions,
    maxSuggestions: 3,
    minSuggestions: 2
  })


  useEffect(() => {
    console.log(visibleMessages, "visibleMessages");
  }, [visibleMessages])

  return (
    <div className="h-screen flex flex-col bg-indigo-50">
      {/* App Header - full width, topmost */}
      <header className="w-full bg-gradient-to-r from-indigo-700 via-indigo-600 to-indigo-800 border-indigo-600 py-3 px-8 flex items-center opacity-90">
        <h1 className="text-xl font-semibold text-gray-300 tracking-tight">AI Stock Analyst</h1>
      </header>
      <div className="flex-1 flex flex-col lg:flex-row" style={{ height: "90vh" }}>
        {/* Left Panel */}
        <div className="w-full lg:w-2/3 p-10 overflow-y-auto hide-scrollbar">
          <div className="flex flex-col gap-8 h-full">
            {data.length > 0 ? (
              <>
                {data.map((item) => {
                  return (
                    <>
                      {/* {Bar Chart data} */}
                      {item.type === "barChart" && <div className="bg-white rounded-xl shadow p-6 border-t-4 border-indigo-500">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xl font-semibold text-black">{item.topic}</span>
                        </div>
                        <div className="text-xs text-gray-700 mb-4">Generated {item.date}</div>
                        {item.data.length > 0 && <CustomBarChart data={item.data} xKey={"x"} barKey={"y"} barLabel={item.topic} />}
                      </div>}

                      {/* {Table data} */}
                      {item.type === "table" && <div className="bg-white rounded-xl shadow p-6 border-t-4 border-indigo-500">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xl font-semibold text-black">{item.topic}</span>
                        </div>
                        <div className="text-xs text-gray-700 mb-4">Generated {item.date}</div>
                        {item.columns.length > 0 && item.rows.length > 0 && <Table size="lg" className="bg-white" columns={item.columns} rows={item.rows} />}

                      </div>}

                      {/* {Line Chart data} */}
                      {item.type === "lineChart" && <div className="bg-white rounded-xl shadow p-6 border-t-4 border-indigo-500">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xl font-semibold text-black">{item.topic}</span>
                        </div>
                        <div className="text-xs text-gray-700 mb-4">Generated {item.date}</div>
                        {item.xArr.length > 0 && item.items.length > 0 && <CustomLineChart data={item.items} xarr={item.xArr} />}
                      </div>}
                    </>
                  )
                })}
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-gray-500">
                <span className="mb-4 text-md font-semibold">No visualization to see. Click any of the suggestions below.</span>
                <ul className="space-y-2">
                  <li>
                    <button
                      disabled={data.length > 0}
                      className="px-5 py-2 rounded-full bg-indigo-50 text-gray-500 text-sm font-medium shadow-sm hover:bg-indigo-100 transition border border-indigo-100"
                      onClick={() => {
                        appendMessage(new TextMessage({
                          content: "Get me the revenue data for Amazon Inc for the last 4 years and show it in a bar chart",
                          role: Role.User
                        }))
                      }}
                    >
                      Show Amazon Revenue (Last 4 Years)
                    </button>
                  </li>
                  <li>
                    <button
                      disabled={data.length > 0}
                      className="px-5 py-2 rounded-full bg-indigo-50 text-gray-500 text-sm font-medium shadow-sm hover:bg-indigo-100 transition border border-indigo-100"
                      onClick={() => {
                        appendMessage(new TextMessage({
                          content: "Get me the top 10 stock performers and show it in a table",
                          role: Role.User
                        }))
                      }}
                    >
                      Show Top 10 Stock Performers
                    </button>
                  </li>
                  <li>
                    <button
                      disabled={data.length > 0}
                      className="px-5 py-2 rounded-full bg-indigo-50 text-gray-500 text-sm font-medium shadow-sm hover:bg-indigo-100 transition border border-indigo-100"
                      onClick={() => {
                        appendMessage(new TextMessage({
                          content: "Compare Apple and Tesla Stocks for the last 2 years and show it in a line chart",
                          role: Role.User
                        }))
                      }}
                    >
                      Compare Apple and Tesla Stocks
                    </button>
                  </li>
                  {/* Add more suggestions as needed */}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel */}
        <div className="lg:w-1/3">
          <CopilotChat
            labels={{
              initial: initialMessage,
            }}
            className="h-full"
          />
        </div>
      </div>
    </div>
  );
}
