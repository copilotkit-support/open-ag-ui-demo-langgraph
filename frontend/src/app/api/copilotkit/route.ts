import {
  CopilotRuntime,
  copilotRuntimeNextJSAppRouterEndpoint,
  OpenAIAdapter,
  GoogleGenerativeAIAdapter
} from '@copilotkit/runtime';
import { NextRequest } from 'next/server';
import { HttpAgent } from "@ag-ui/client";


const langgraphAgent = new HttpAgent({
  url: process.env.NEXT_PUBLIC_LANGGRAPH_URL || "http://0.0.0.0:8000/langgraph-agent",
});
const serviceAdapter = new GoogleGenerativeAIAdapter()
const runtime = new CopilotRuntime({
  agents: {
    // @ts-ignore
    langgraphAgent : langgraphAgent 
  },
});
// const runtime = new CopilotRuntime()
export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: '/api/copilotkit',
  });

  return handleRequest(req);
};