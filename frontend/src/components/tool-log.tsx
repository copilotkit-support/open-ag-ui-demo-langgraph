import React, { useEffect } from "react";

interface ToolLogInterface {
    toolName: string;
    status: "inProgress" | "completed";
}

interface ToolLogProps {
    state: ToolLogInterface[];
}

const LoaderText: React.FC<{ text: string }> = ({ text }) => (
    <span className="relative inline-block font-medium">
        {/* Muted base text */}
        <span className="text-gray-400 select-none">{text}</span>
        {/* Animated mask for unmuted text */}
        <span className="absolute left-0 top-0 w-full h-full pointer-events-none overflow-hidden" aria-hidden="true">
            <span
                className="absolute top-0 h-full w-1/3 animate-loader-mask"
                style={{
                    background: "linear-gradient(to right, transparent 0%, #fff 40%, #fff 60%, transparent 100%)",
                    WebkitBackgroundClip: "text",
                    color: "#facc15", // yellow-400
                    WebkitTextFillColor: "transparent",
                }}
            >
                <span className="font-medium text-yellow-600" style={{ WebkitTextFillColor: "inherit" }}>{text}</span>
            </span>
            <style>{`
        @keyframes loader-mask {
          0% { left: 0; }
          100% { left: 66%; }
        }
        .animate-loader-mask {
          animation: loader-mask 1.2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
      `}</style>
        </span>
    </span>
);

const TickIcon = () => (
    <span className="flex items-center justify-center w-7 h-7 rounded-full bg-indigo-100 border border-indigo-200 ml-2">
        <svg className="w-4 h-4 text-indigo-500" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
    </span>
);

const StatusTag: React.FC<{ status: "inProgress" | "completed" }> = ({ status }) => (
    <span className="ml-2 flex items-center">
        <span className="rounded-full bg-gray-200 text-gray-700 text-[10px] font-semibold px-2 py-0.5">
            {status === "inProgress" ? "Running" : "Completed"}
        </span>
    </span>
);

const ToolLog: React.FC<ToolLogProps> = ({ state }) => {
    useEffect(() => {
        console.log(state, "stateInsideToolLog");
        console.log(state.reverse(), "stateInsideToolLogReverse");
    }, [state])
    return (
        <>
            {state.reverse().map((item) => (
                <div
                    className={`mt-2 flex items-center justify-between gap-2 px-4 py-2 rounded-lg shadow border transition-all duration-300 pl-8
         ${item.status === "completed" ? "border-indigo-500 bg-white border-r-4" : ""}
         ${item.status === "completed" ? "pr-3" : ""}
         ${item.status === "inProgress" ? "border-yellow-400 bg-yellow-50 border-r-4" : ""}
       `}
                    style={item.status === "completed" ? { borderRightWidth: '4px' } : item.status === "inProgress" ? { borderRightWidth: '4px' } : {}}
                >
                    <div className="flex items-center gap-2 flex-1">
                        {item.status === "inProgress" ? (
                            <LoaderText text={item.toolName} />
                        ) : (
                            <span className="font-medium text-indigo-700">
                                {item.toolName}
                            </span>
                        )}
                    </div>
                    <StatusTag status={item.status} />
                    <div className="flex items-center gap-1">
                        {item.status === "completed" && <TickIcon />}
                    </div>
                </div>
            ))}
        </>
    );
};

export default ToolLog;
