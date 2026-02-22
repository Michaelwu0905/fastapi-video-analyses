import { ref } from 'vue'
import axios from 'axios'

export function useVideoAnalysis() {
    const videoUrl = ref('https://www.bilibili.com/video/BV1GJ411x7h7')
    const loading = ref(false)
    const videoInfo = ref(null)
    const errorMsg = ref(null)

    const analyzeVideo = async ({ onHasComments, onReset } = {}) => {
        if (!videoUrl.value.trim()) return

        loading.value = true
        videoInfo.value = null
        errorMsg.value = null
        onReset?.()

        try {
            const response = await axios.post('/api/analyze', { url: videoUrl.value })
            videoInfo.value = response.data

            if (videoInfo.value.saved_comments_count > 0) {
                onHasComments?.()
            }
        } catch (err) {
            errorMsg.value = err.response?.data?.detail ?? '无法连接到后端服务器'
        } finally {
            loading.value = false
        }
    }

    return { videoUrl, loading, videoInfo, errorMsg, analyzeVideo }
}
