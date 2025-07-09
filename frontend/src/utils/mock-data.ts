export interface PortfolioState {
  id: string
  trigger: string
  investmentAmount?: number
  currentPortfolioValue?: number
  performanceData: Array<{
    date: string
    portfolio: number
    spy: number
  }>
  allocations: Array<{
    ticker: string
    allocation: number
    currentValue: number
    totalReturn: number
  }>
  returnsData: Array<{
    ticker: string
    return: number
  }>
  bullInsights: Array<{
    title: string
    description: string
    emoji: string
  }>
  bearInsights: Array<{
    title: string
    description: string
    emoji: string
  }>
}

export const mockPortfolioStates: PortfolioState[] = [
  {
    id: "aapl-nvda",
    trigger: "apple nvidia",
    performanceData: [
      { date: "Jan 2023", portfolio: 10000, spy: 10000 },
      { date: "Mar 2023", portfolio: 10800, spy: 10200 },
      { date: "Jun 2023", portfolio: 12500, spy: 11000 },
      { date: "Sep 2023", portfolio: 11800, spy: 10800 },
      { date: "Dec 2023", portfolio: 13250, spy: 11500 },
      { date: "Mar 2024", portfolio: 14100, spy: 12200 },
      { date: "Jun 2024", portfolio: 15800, spy: 12800 },
      { date: "Sep 2024", portfolio: 16200, spy: 13100 },
      { date: "Dec 2024", portfolio: 17500, spy: 13600 },
    ],
    allocations: [
      { ticker: "AAPL", allocation: 50, currentValue: 8750, totalReturn: 32.5 },
      { ticker: "NVDA", allocation: 50, currentValue: 8750, totalReturn: 85.2 },
    ],
    returnsData: [
      { ticker: "AAPL", return: 32.5 },
      { ticker: "NVDA", return: 85.2 },
    ],
    bullInsights: [
      {
        title: "AI Revolution Momentum",
        description:
          "NVIDIA's dominance in AI chips positions the portfolio perfectly for continued growth as AI adoption accelerates across industries.",
        emoji: "🚀",
      },
      {
        title: "Apple's Services Growth",
        description:
          "Apple's expanding services revenue provides stable, high-margin income that supports long-term valuation growth.",
        emoji: "📱",
      },
    ],
    bearInsights: [
      {
        title: "NVIDIA Valuation Concerns",
        description:
          "Current AI hype may have inflated NVIDIA beyond sustainable levels, with P/E ratios suggesting potential correction risk.",
        emoji: "⚠️",
      },
      {
        title: "Tech Sector Concentration",
        description:
          "Heavy concentration in tech stocks exposes portfolio to sector-wide downturns and regulatory risks.",
        emoji: "📉",
      },
    ],
  },
  {
    id: "tsla-msft",
    trigger: "tesla microsoft",
    performanceData: [
      { date: "Jan 2023", portfolio: 5000, spy: 5000 },
      { date: "Mar 2023", portfolio: 5200, spy: 5100 },
      { date: "Jun 2023", portfolio: 5800, spy: 5500 },
      { date: "Sep 2023", portfolio: 5400, spy: 5400 },
      { date: "Dec 2023", portfolio: 6100, spy: 5750 },
      { date: "Mar 2024", portfolio: 6800, spy: 6100 },
      { date: "Jun 2024", portfolio: 7200, spy: 6400 },
      { date: "Sep 2024", portfolio: 7500, spy: 6550 },
      { date: "Dec 2024", portfolio: 7850, spy: 6800 },
    ],
    allocations: [
      { ticker: "TSLA", allocation: 50, currentValue: 3925, totalReturn: 28.5 },
      { ticker: "MSFT", allocation: 50, currentValue: 3925, totalReturn: 42.8 },
    ],
    returnsData: [
      { ticker: "TSLA", return: 28.5 },
      { ticker: "MSFT", return: 42.8 },
    ],
    bullInsights: [
      {
        title: "EV Market Leadership",
        description:
          "Tesla's first-mover advantage in EVs and energy storage creates sustainable competitive moats as the world transitions to clean energy.",
        emoji: "🔋",
      },
      {
        title: "Microsoft Cloud Dominance",
        description:
          "Azure's rapid growth and AI integration through OpenAI partnership positions Microsoft for continued enterprise expansion.",
        emoji: "☁️",
      },
    ],
    bearInsights: [
      {
        title: "Tesla Competition Intensifies",
        description:
          "Traditional automakers and new EV entrants are rapidly closing the gap, potentially eroding Tesla's market share and margins.",
        emoji: "🏁",
      },
      {
        title: "Cloud Market Saturation",
        description:
          "Slowing cloud growth rates and increased competition from AWS and Google Cloud may pressure Microsoft's margins.",
        emoji: "📊",
      },
    ],
  },
  {
    id: "amzn-googl",
    trigger: "amazon google",
    performanceData: [
      { date: "Jan 2023", portfolio: 15000, spy: 15000 },
      { date: "Mar 2023", portfolio: 15600, spy: 15300 },
      { date: "Jun 2023", portfolio: 17200, spy: 16500 },
      { date: "Sep 2023", portfolio: 16800, spy: 16200 },
      { date: "Dec 2023", portfolio: 18500, spy: 17250 },
      { date: "Mar 2024", portfolio: 19800, spy: 18300 },
      { date: "Jun 2024", portfolio: 21200, spy: 19200 },
      { date: "Sep 2024", portfolio: 20800, spy: 19650 },
      { date: "Dec 2024", portfolio: 22100, spy: 20400 },
    ],
    allocations: [
      { ticker: "AMZN", allocation: 50, currentValue: 11050, totalReturn: 38.2 },
      { ticker: "GOOGL", allocation: 50, currentValue: 11050, totalReturn: 52.4 },
    ],
    returnsData: [
      { ticker: "AMZN", return: 38.2 },
      { ticker: "GOOGL", return: 52.4 },
    ],
    bullInsights: [
      {
        title: "AWS Profit Engine",
        description:
          "Amazon's cloud division continues generating massive margins that subsidize retail expansion and fuel innovation investments.",
        emoji: "💰",
      },
      {
        title: "Search Advertising Moat",
        description:
          "Google's search dominance creates an unassailable advertising revenue stream with consistent growth potential.",
        emoji: "🔍",
      },
    ],
    bearInsights: [
      {
        title: "Retail Margin Pressure",
        description:
          "Amazon's core retail business faces increasing competition and logistics costs that could compress overall profitability.",
        emoji: "📦",
      },
      {
        title: "AI Search Disruption Risk",
        description:
          "ChatGPT and AI-powered search alternatives threaten Google's core search business model and advertising revenues.",
        emoji: "🤖",
      },
    ],
  },
  {
    id: "meta-nflx",
    trigger: "meta netflix",
    performanceData: [
      { date: "Jan 2023", portfolio: 8000, spy: 8000 },
      { date: "Mar 2023", portfolio: 8400, spy: 8160 },
      { date: "Jun 2023", portfolio: 9200, spy: 8800 },
      { date: "Sep 2023", portfolio: 8900, spy: 8640 },
      { date: "Dec 2023", portfolio: 10100, spy: 9200 },
      { date: "Mar 2024", portfolio: 11200, spy: 9760 },
      { date: "Jun 2024", portfolio: 12000, spy: 10240 },
      { date: "Sep 2024", portfolio: 11600, spy: 10480 },
      { date: "Dec 2024", portfolio: 12800, spy: 10880 },
    ],
    allocations: [
      { ticker: "META", allocation: 50, currentValue: 6400, totalReturn: 68.5 },
      { ticker: "NFLX", allocation: 50, currentValue: 6400, totalReturn: 24.2 },
    ],
    returnsData: [
      { ticker: "META", return: 68.5 },
      { ticker: "NFLX", return: 24.2 },
    ],
    bullInsights: [
      {
        title: "Metaverse Pioneer Advantage",
        description:
          "Meta's early investment in VR/AR technology positions it to capture the next computing platform as the metaverse develops.",
        emoji: "🥽",
      },
      {
        title: "Netflix Content Moat",
        description:
          "Netflix's global content library and production capabilities create sustainable competitive advantages in streaming.",
        emoji: "🎬",
      },
    ],
    bearInsights: [
      {
        title: "Metaverse Uncertainty",
        description:
          "Meta's massive metaverse investments may not pay off if consumer adoption remains slow or the technology fails to mature.",
        emoji: "🌫️",
      },
      {
        title: "Streaming Competition",
        description:
          "Intense competition from Disney+, HBO Max, and others fragments the market and increases Netflix's content costs.",
        emoji: "📺",
      },
    ],
  },
]
