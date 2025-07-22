import * as React from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';
import Box from '@mui/material/Box';
import { BarChart } from '@mui/x-charts/BarChart';
import { useTheme } from '@mui/material/styles';
import axios from 'axios';

export default function PageViewsBarChart() {
  const [xAxisUrls, setXAxisUrls] = React.useState([]);  // Array of url_id, sorted by rank
  const [redData, setRedData] = React.useState([]);       // For CTR=0 (red bars)
  const [greenData, setGreenData] = React.useState([]);     // For CTR>0 (green bars)
  const [totalViews, setTotalViews] = React.useState(0);    // Total CTR value (for display)

  const theme = useTheme();

  // Memoize fetchData so that it is stable between renders.
  const fetchData = React.useCallback(() => {
    const token = localStorage.getItem("session_token") || "";
    const headers = { Authorization: token };

    Promise.all([
      axios.get("/api/mab_rank_logs", { headers }),
      axios.get("/api/office_mab_stats", { headers }),
    ])
      .then(([logsResp, statsResp]) => {
        const mabLogs = logsResp.data.mab_rank_logs || [];
        const officeStats = statsResp.data.office_mab_stats || [];

        // Build a mapping from url_id to the lowest rank_position.
        const rankMap = {};
        mabLogs.forEach((row) => {
          const { url_id, rank_position } = row;
          if (!(url_id in rankMap) || rank_position < rankMap[url_id]) {
            rankMap[url_id] = rank_position;
          }
        });

        // Build a mapping from url_id to the maximum CTR, converting values to numbers.
        const ctrMap = {};
        officeStats.forEach((row) => {
          const { url_id, office_ctr } = row;
          const ctrValue = Number(office_ctr);
          if (!(url_id in ctrMap)) {
            ctrMap[url_id] = ctrValue;
          } else {
            ctrMap[url_id] = Math.max(ctrMap[url_id], ctrValue);
          }
        });

        // Sort the url_ids by their rank.
        const sortedUrls = Object.keys(rankMap).sort(
          (a, b) => rankMap[a] - rankMap[b]
        );

        // Build the data arrays for the bar chart.
        // For articles with 0 CTR, push a default 0.1 for the red series to ensure the bar is visible.
        const redSeries = [];
        const greenSeries = [];
        let total = 0;
        sortedUrls.forEach((u) => {
          const val = Number(ctrMap[u]) || 0;
          if (val === 0) {
            redSeries.push(0.01);
            greenSeries.push(null);
          } else {
            redSeries.push(null);
            greenSeries.push(val);
          }
          total += val;
        });

        setXAxisUrls(sortedUrls);
        setRedData(redSeries);
        setGreenData(greenSeries);
        setTotalViews(total.toFixed(1));
      })
      .catch((err) => {
        console.error("Error fetching data for bar chart:", err);
      });
  }, []); // No dependencies, so this function remains stable

  // Set up polling with a 10-second interval.
  React.useEffect(() => {
    console.log("Setting interval for fetchData");
    fetchData(); // Initial fetch
    const interval = setInterval(() => {
      console.log("Polling fetchData");
      fetchData();
    }, 1000); // 1 seconds
    return () => {
      console.log("Clearing interval for fetchData");
      clearInterval(interval);
    };
  }, [fetchData]);

  // Calculate dynamic width based on the number of x-axis items.
  const barWidth = 20;
  const dynamicWidth = Math.max(800, xAxisUrls.length * barWidth);

  return (
    <Card variant="outlined" sx={{ width: '100%' }}>
      <CardContent>
       {/* <Typography component="h2" variant="subtitle2" gutterBottom>
          CTR by URL (Ordered by Rank)
        </Typography>
        <Stack direction="row" alignItems="center" gap={1} sx={{ mb: 1 }}>
          <Typography variant="h4" component="p">
            {totalViews}
          </Typography>
          <Chip size="small" color="success" label="+12%" />
        </Stack>
        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
          Sum of CTR values for demonstration
        </Typography> */}
        {/* Outer container with horizontal scrolling */}
        <Box sx={{ mt: 2, overflowX: 'auto' }}>
          {/* Inner container with dynamic width */}
          <Box sx={{ width: dynamicWidth }}>
            <BarChart
              height={300}
              margin={{ left: 50, right: 10, top: 20, bottom: 40 }}
              xAxis={[
                {
                  scaleType: 'band',
                  categoryGapRatio: 0.4,
                  data: xAxisUrls,
                },
              ]}
              yAxis={[
                {
                  domain: [0, 5],
                },
              ]}
              series={[
                {
                  id: 'zero-ctr',
                  label: 'CTR=0',
                  data: redData,
                  stack: 'ctrStack',
                  color: 'red',
                },
                {
                  id: 'nonzero-ctr',
                  label: 'CTR>0',
                  data: greenData,
                  stack: 'ctrStack',
                  color: 'green',
                },
              ]}
              grid={{ horizontal: true }}
              slotProps={{
                legend: { hidden: true },
              }}
            />
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}
