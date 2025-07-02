import React from "react";

interface TableProps {
  columns: string[];
  rows: { row_data: string[] }[];
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
    <div className={`overflow-x-auto rounded-lg border border-[color:var(--foreground)]/10 bg-[color:var(--background)] ${className}`}>
      <table className="min-w-full divide-y divide-[color:var(--foreground)]/10">
        <thead className="bg-[color:var(--background)]">
          <tr>
            {columns?.map((col, idx) => (
              <th
                key={idx}
                className={`font-semibold text-left text-[color:var(--foreground)] ${cellClass}`}
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-[color:var(--background)]">
          {rows?.map((row, i) => (
            <tr
              key={i}
              className={
                i % 2 === 0
                  ? "bg-[color:var(--background)]"
                  : "bg-[color:var(--foreground)]/5"
              }
            >
              {row?.row_data?.map((cell, j) => (
                <td
                  key={j}
                  className={`text-[color:var(--foreground)] ${cellClass}`}
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
