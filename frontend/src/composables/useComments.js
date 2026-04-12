import { ref } from 'vue'
import axios from 'axios'

export function useComments() {
    const fetchingComments = ref(false)
    const fetchStatus = ref(null)
    const showComments = ref(false)
    const loadingComments = ref(false)
    const commentsList = ref([])
    const maxComments = ref(200)

    const reset = () => {
        fetchStatus.value = null
        showComments.value = false
        commentsList.value = []
    }

    // loadCommentsList 需要 bvid 和外部的 sentimentStats setter
    const loadCommentsList = async ({ bvid, onStatsLoaded, onKnowledgeEffectLoaded }) => {
        if (!bvid) return

        loadingComments.value = true
        try {
            const response = await axios.get(`/api/sentiment/${bvid}`)
            commentsList.value = response.data.comments
            onStatsLoaded?.(response.data.stats)
            onKnowledgeEffectLoaded?.(response.data.knowledge_effect ?? null)
        } catch (err) {
            console.warn('获取情感分析结果失败，回退到普通列表', err)
            const response = await axios.get(`/api/comments/${bvid}`)
            commentsList.value = response.data.comments
        } finally {
            loadingComments.value = false
        }
    }

    const fetchComments = async ({ videoInfo, onStatsLoaded, onKnowledgeEffectLoaded, onStartPolling, onResetSentiment }) => {
        if (!videoInfo) return

        const requestedMaxComments = Math.min(Math.max(Number(maxComments.value) || 200, 20), 5000)
        maxComments.value = requestedMaxComments
        fetchingComments.value = true
        fetchStatus.value = { type: 'info', msg: `正在按最大抓取数采集一级评论，最多 ${requestedMaxComments} 条，请稍候...` }
        onResetSentiment?.()

        try {
            const response = await axios.post('/api/fetch-comments', {
                bvid: videoInfo.bvid,
                aid: videoInfo.aid,
                max_comments: requestedMaxComments,
            })
            fetchStatus.value = {
                type: 'success',
                msg: `最多请求 ${response.data.effective_max_comments} 条，实际抓取 ${response.data.total_fetched} 条，保存 ${response.data.saved_count} 条；${response.data.stopped_reason}`,
            }
            videoInfo.saved_comments_count = response.data.saved_count

            await loadCommentsList({ bvid: videoInfo.bvid, onStatsLoaded, onKnowledgeEffectLoaded })
            showComments.value = true
            onStartPolling?.()
        } catch (err) {
            fetchStatus.value = {
                type: 'error',
                msg: err.response?.data?.detail ?? '爬取评论失败',
            }
        } finally {
            fetchingComments.value = false
        }
    }

    const toggleCommentsList = async ({ bvid, onStatsLoaded, onKnowledgeEffectLoaded }) => {
        if (showComments.value) {
            showComments.value = false
        } else {
            showComments.value = true
            if (commentsList.value.length === 0) {
                await loadCommentsList({ bvid, onStatsLoaded, onKnowledgeEffectLoaded })
            }
        }
    }

    return {
        fetchingComments,
        fetchStatus,
        showComments,
        loadingComments,
        commentsList,
        maxComments,
        reset,
        loadCommentsList,
        fetchComments,
        toggleCommentsList,
    }
}
