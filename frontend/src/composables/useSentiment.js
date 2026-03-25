import { ref } from 'vue'
import axios from 'axios'

export function useSentiment() {
    const sentimentStats = ref(null)
    const knowledgeEffect = ref(null)
    const sentimentPolling = ref(false)
    const sentimentTimer = ref(null)

    const stopSentimentPolling = () => {
        sentimentPolling.value = false
        if (sentimentTimer.value) {
            clearInterval(sentimentTimer.value)
            sentimentTimer.value = null
        }
    }

    const reset = () => {
        sentimentStats.value = null
        knowledgeEffect.value = null
        stopSentimentPolling()
    }

    // 返回一个 checkFn 以便外部调用（checkFn 需要访问 bvid 和 loadCommentsList）
    const buildCheckFn = ({ getBvid, onFinished }) => {
        return async () => {
            const bvid = getBvid()
            if (!bvid) return

            try {
                const { data } = await axios.get(`/api/sentiment-status/${bvid}`)
                const { total, analyzed, finished } = data

                if (!sentimentStats.value) {
                    sentimentStats.value = { total, analyzed, pending: total - analyzed }
                } else {
                    sentimentStats.value.total = total
                    sentimentStats.value.analyzed = analyzed
                    sentimentStats.value.pending = total - analyzed
                }

                if (finished) {
                    stopSentimentPolling()
                    await onFinished?.()
                }
            } catch (err) {
                console.error('轮询情感状态失败:', err)
                stopSentimentPolling()
            }
        }
    }

    const startSentimentPolling = (checkFn) => {
        if (sentimentPolling.value) return
        sentimentPolling.value = true
        sentimentTimer.value = setInterval(checkFn, 3000)
    }

    return {
        sentimentStats,
        knowledgeEffect,
        sentimentPolling,
        reset,
        buildCheckFn,
        startSentimentPolling,
        stopSentimentPolling,
    }
}
