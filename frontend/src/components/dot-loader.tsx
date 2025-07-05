import React from "react";

const DotLoader: React.FC<{ className?: string }> = ({ className = "" }) => {
  return (
    <div className={`flex items-center mt-4 space-x-2 ${className}`}>
      <span className="block w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:-0.32s]"></span>
      <span className="block w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:-0.16s]"></span>
      <span className="block w-2 h-2 bg-gray-500 rounded-full animate-bounce"></span>
    </div>
  );
};

export default DotLoader;
