import { Box } from '@mui/material'
import { Doughnut } from 'react-chartjs-2'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { AgentType } from '@types/index'

ChartJS.register(ArcElement, Tooltip, Legend)

interface CallDistributionChartProps {
  data: Record<AgentType, number>
}

const agentColors = {
  [AgentType.GENERAL]: '#2196F3',
  [AgentType.BILLING]: '#4CAF50',
  [AgentType.SUPPORT]: '#FF9800',
  [AgentType.SALES]: '#9C27B0',
  [AgentType.SCHEDULING]: '#00BCD4',
}

export default function CallDistributionChart({ data }: CallDistributionChartProps) {
  const chartData = {
    labels: Object.keys(data).map((key) => 
      key.charAt(0).toUpperCase() + key.slice(1)
    ),
    datasets: [
      {
        data: Object.values(data),
        backgroundColor: Object.keys(data).map((key) => agentColors[key as AgentType]),
        borderWidth: 0,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
    },
  }

  return (
    <Box sx={{ height: 300 }}>
      <Doughnut data={chartData} options={options} />
    </Box>
  )
}