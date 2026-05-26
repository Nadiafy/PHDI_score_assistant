<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-3xl font-bold text-gray-900">30-Day PHDI Trend</h1>
      <div class="bg-white px-6 py-3 rounded-xl shadow-sm border border-gray-100">
         <span class="text-sm text-gray-500 font-medium">Average Score</span>
         <div class="text-2xl font-bold text-green-600">{{ averageScore }} <span class="text-sm font-normal text-gray-400">/ 150</span></div>
      </div>
    </div>

    <!-- Chart -->
    <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 h-96 relative">
      <Line
        v-if="chartData.datasets.length > 0"
        :data="chartData"
        :options="chartOptions"
      />
      <div v-else class="absolute inset-0 flex items-center justify-center text-gray-400 font-medium pb-8 flex-col space-y-4">
         <div class="text-4xl text-gray-200">📊</div>
         <p>No data recorded yet. Head to the Chatbot to log a meal!</p>
      </div>
    </div>

    <!-- History Table -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden mt-8">
       <table class="min-w-full divide-y divide-gray-200">
         <thead class="bg-gray-50">
           <tr>
             <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
             <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Score</th>
             <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
           </tr>
         </thead>
         <tbody class="bg-white divide-y divide-gray-200">
           <tr v-for="log in history" :key="log.date" class="hover:bg-gray-50 transition-colors">
             <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">{{ log.date }}</td>
             <td class="px-6 py-4 whitespace-nowrap text-sm font-bold" :class="log.total_phdi_score > 75 ? 'text-green-600' : 'text-orange-500'">{{ log.total_phdi_score }} / 150</td>
             <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
               <span v-if="log.total_phdi_score >= 120" class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Excellent</span>
               <span v-else-if="log.total_phdi_score >= 75" class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">Good</span>
               <span v-else class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-orange-100 text-orange-800">Needs Work</span>
             </td>
           </tr>
         </tbody>
       </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { Line } from 'vue-chartjs'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

definePageMeta({ layout: 'dashboard' })

const history = ref([])

onMounted(async () => {
   const token = localStorage.getItem('auth_token')
   if (!token) return

   try {
     const res = await fetch('http://localhost:8000/api/history/recent', {
       headers: { 'Authorization': `Bearer ${token}` }
     })
     const data = await res.json()
     if(Array.isArray(data)) {
       history.value = data
     }
   } catch (e) {
     console.error(e)
   }
})

const averageScore = computed(() => {
   if (history.value.length === 0) return 0
   const sum = history.value.reduce((acc, curr) => acc + curr.total_phdi_score, 0)
   return (sum / history.value.length).toFixed(1)
})

const chartData = computed(() => {
   if (history.value.length === 0) return { datasets: [] }
   return {
     labels: history.value.map(h => h.date),
     datasets: [
       {
         label: 'Daily PHDI',
         data: history.value.map(h => h.total_phdi_score),
         borderColor: '#10b981', // emerald-500
         backgroundColor: 'rgba(16, 185, 129, 0.1)',
         borderWidth: 3,
         pointBackgroundColor: '#fff',
         pointBorderColor: '#10b981',
         pointBorderWidth: 2,
         pointRadius: 4,
         pointHoverRadius: 6,
         fill: true,
         tension: 0.4
       }
     ]
   }
})

const chartOptions = {
   responsive: true,
   maintainAspectRatio: false,
   scales: {
     y: {
       min: 0,
       max: 150,
       grid: {
         color: '#f3f4f6',
         drawBorder: false,
       },
       ticks: {
          color: '#6b7280',
          font: { family: "'Inter', sans-serif" }
       }
     },
     x: {
       grid: { display: false },
       ticks: {
          color: '#6b7280',
          font: { family: "'Inter', sans-serif" }
       }
     }
   },
   plugins: {
     legend: { display: false },
     tooltip: {
        backgroundColor: '#1f2937',
        padding: 12,
        titleFont: { family: "'Inter', sans-serif", size: 14 },
        bodyFont: { family: "'Inter', sans-serif", size: 13, weight: 'bold' },
        displayColors: false,
        callbacks: {
           label: (context) => `${context.parsed.y} points`
        }
     }
   },
   interaction: {
      intersect: false,
      mode: 'index',
   },
}
</script>
