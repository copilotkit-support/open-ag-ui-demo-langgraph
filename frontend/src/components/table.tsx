import React from "react";

interface TableProps {
  columns: string[];
  rows: { row_data: (string|number)[] }[];
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeClasses = {
  sm: "text-xs px-2 py-1",
  md: "text-sm px-4 py-2",
  lg: "text-base px-6 py-3",
};

export const Table: React.FC<TableProps> = ({ columns, rows, size = "md", className = "" }) => {
  const cellClass = sizeClasses[size];
  return (
    <div className={`overflow-x-auto rounded-lg border border-gray-200 bg-white ${className}`}>
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-white">
          <tr>
            {columns?.map((col, idx) => (
              <th
                key={idx}
                className={`font-semibold text-left text-black ${cellClass}`}
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white">
          {rows?.map((row, i) => (
            <tr
              key={i}
              className={
                i % 2 === 0
                  ? "bg-white"
                  : "bg-gray-50"
              }
            >
              {row.row_data?.map((cell, j) => (
                <td
                  key={j}
                  className={`text-black ${cellClass}`}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Table;
