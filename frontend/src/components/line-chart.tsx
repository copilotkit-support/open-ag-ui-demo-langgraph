"use client"
import React, { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

interface LineChartProps {
    data: any[];
    lineColors?: string[];
    height?: number;
    legend?: boolean;
    xarr: string[];
}

const CustomLineChart: React.FC<LineChartProps> = ({
    data,
    lineColors = ["#6366F1", "#F59E42", "#10B981", "#EF4444"],
    height = 300,
    legend = true,
    xarr,
}) => {
    return (
        <ResponsiveContainer width="100%" height={height}>
            <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey={'name'} />
                <YAxis />
                <Tooltip />
                {legend && <Legend />}
                {xarr.map((key, idx) => (
                    <Line
                        key={key}
                        type="monotone"
                        dataKey={key}
                        stroke={lineColors[idx % lineColors.length]}
                        strokeWidth={2}
                        dot={false}
                        isAnimationActive={false}
                    />
                ))}
            </LineChart>
        </ResponsiveContainer>
    );
};

export default CustomLineChart;
