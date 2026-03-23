import { ref } from 'vue'
import axios from 'axios'

export function useVideoAnalysis() {
    const videoUrl = ref('https://www.bilibili.com/video/BV1GJ411x7h7')
    const loading = ref(false)
    const videoInfo = ref(null)
    const contentAnalysis = ref(null)
    const contentAnalysisLoading = ref(false)
    const contentAnalysisError = ref(null)
    const errorMsg = ref(null)

    const analyzeVideo = async ({ onHasComments, onReset } = {}) => {
        if (!videoUrl.value.trim()) return

        loading.value = true
        videoInfo.value = null
        contentAnalysis.value = null
        contentAnalysisError.value = null
        errorMsg.value = null
        onReset?.()

        try {
            const response = await axios.post('/api/analyze', { url: videoUrl.value })
            videoInfo.value = response.data

            contentAnalysisLoading.value = true
            try {
                const contentResponse = await axios.post('/api/content-analysis', { url: videoUrl.value })
                contentAnalysis.value = contentResponse.data.content_analysis
            } catch (err) {
                contentAnalysisError.value = err.response?.data?.detail ?? '无法获取视频内容分析结果'
            } finally {
                contentAnalysisLoading.value = false
            }

            if (videoInfo.value.saved_comments_count > 0) {
                onHasComments?.()
            }
        } catch (err) {
            errorMsg.value = err.response?.data?.detail ?? '无法连接到后端服务器'
        } finally {
            loading.value = false
        }
    }

    return {
        videoUrl,
        loading,
        videoInfo,
        contentAnalysis,
        contentAnalysisLoading,
        contentAnalysisError,
        errorMsg,
        analyzeVideo,
    }
}
