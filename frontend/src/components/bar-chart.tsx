import React from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface BarChartProps {
    data: any[];
    xKey: string;
    barKey: string;
    barLabel?: string;
}

const CustomBarChart: React.FC<BarChartProps> = ({ data, xKey = "x", barKey = "y", barLabel }) => {
    return (
        <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data} >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey={xKey} />
                <YAxis />
                <Tooltip />
                <Bar dataKey={barKey} fill="#8884d8" />
            </BarChart>
        </ResponsiveContainer>
    );
};

export default CustomBarChart;
