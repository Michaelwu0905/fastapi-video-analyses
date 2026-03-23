import { ref } from 'vue'
import axios from 'axios'

export function useVideoAnalysis() {
    const videoUrl = ref('https://www.bilibili.com/video/BV1GJ411x7h7')
    const loading = ref(false)
    const videoInfo = ref(null)
    const contentAnalysis = ref(null)
    const contentAnalysisLoading = ref(false)
    const contentAnalysisError = ref(null)
    const contentAnalysisStatus = ref(null)
    const contentAnalysisTimer = ref(null)
    const errorMsg = ref(null)

    const stopContentAnalysisPolling = () => {
        if (contentAnalysisTimer.value) {
            clearInterval(contentAnalysisTimer.value)
            contentAnalysisTimer.value = null
        }
    }

    const resetContentAnalysis = () => {
        contentAnalysis.value = null
        contentAnalysisError.value = null
        contentAnalysisStatus.value = null
        contentAnalysisLoading.value = false
        stopContentAnalysisPolling()
    }

    const loadRealContentAnalysisResult = async (bvid) => {
        const response = await axios.get(`/api/content-analysis/result/${bvid}`)
        contentAnalysis.value = response.data.content_analysis
        contentAnalysisError.value = null
        contentAnalysisStatus.value = {
            type: 'success',
            msg: '已完成真实视频内容分析',
        }
        contentAnalysisLoading.value = false
    }

    const startRealContentAnalysisPolling = (bvid) => {
        stopContentAnalysisPolling()
        contentAnalysisTimer.value = setInterval(async () => {
            try {
                const { data } = await axios.get(`/api/content-analysis/status/${bvid}`)
                contentAnalysisStatus.value = {
                    type: data.task_status === 'error' ? 'error' : 'info',
                    msg: data.error || data.message,
                }

                if (!data.finished) return

                stopContentAnalysisPolling()

                if (data.task_status === 'success') {
                    await loadRealContentAnalysisResult(bvid)
                    return
                }

                contentAnalysisLoading.value = false
                contentAnalysisError.value = data.error || data.message || '真实视频内容分析失败'
            } catch (err) {
                stopContentAnalysisPolling()
                contentAnalysisLoading.value = false
                contentAnalysisError.value = err.response?.data?.detail ?? '轮询内容分析状态失败'
                contentAnalysisStatus.value = {
                    type: 'error',
                    msg: contentAnalysisError.value,
                }
            }
        }, 5000)
    }

    const startRealContentAnalysis = async ({ url, bvid }) => {
        contentAnalysisLoading.value = true
        contentAnalysisError.value = null
        contentAnalysisStatus.value = {
            type: 'info',
            msg: '正在准备真实视频内容分析任务...',
        }

        try {
            const { data } = await axios.post('/api/content-analysis/start-real', { url })
            const taskBvid = data.bvid || bvid

            if (data.task_status === 'success' && data.content_analysis) {
                contentAnalysis.value = data.content_analysis
                contentAnalysisLoading.value = false
                contentAnalysisStatus.value = {
                    type: 'success',
                    msg: '已命中缓存的真实视频内容分析结果',
                }
                return
            }

            contentAnalysisStatus.value = {
                type: 'info',
                msg: data.message || '真实视频内容分析任务已启动',
            }
            startRealContentAnalysisPolling(taskBvid)
        } catch (err) {
            contentAnalysisLoading.value = false
            contentAnalysisError.value = err.response?.data?.detail ?? '无法启动真实视频内容分析'
            contentAnalysisStatus.value = {
                type: 'error',
                msg: contentAnalysisError.value,
            }
        }
    }

    const analyzeVideo = async ({ onHasComments, onReset } = {}) => {
        if (!videoUrl.value.trim()) return

        loading.value = true
        videoInfo.value = null
        resetContentAnalysis()
        errorMsg.value = null
        onReset?.()

        try {
            const response = await axios.post('/api/analyze', { url: videoUrl.value })
            videoInfo.value = response.data

            contentAnalysisLoading.value = true
            try {
                const contentResponse = await axios.post('/api/content-analysis', { url: videoUrl.value })
                contentAnalysis.value = contentResponse.data.content_analysis
                contentAnalysisStatus.value = {
                    type: 'success',
                    msg: '已加载本地索引内容分析结果',
                }
            } catch (err) {
                const detail = err.response?.data?.detail ?? '无法获取视频内容分析结果'
                if (err.response?.status === 404) {
                    await startRealContentAnalysis({ url: videoUrl.value, bvid: videoInfo.value.bvid })
                } else {
                    contentAnalysisError.value = detail
                    contentAnalysisStatus.value = {
                        type: 'error',
                        msg: detail,
                    }
                }
            } finally {
                if (!contentAnalysisTimer.value) {
                    contentAnalysisLoading.value = false
                }
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
        contentAnalysisStatus,
        errorMsg,
        analyzeVideo,
    }
}
