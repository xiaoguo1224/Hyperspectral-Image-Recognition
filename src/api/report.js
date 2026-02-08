import request from '@/utils/request'

export function cubeView(data) {
    return request({
        url: '/report/cube',
        method: 'post',
        data: data
    })
}

// 导出 PDF
export function exportReportPdf(taskId) {
    return request({
        url: '/report/export/' + taskId,
        method: 'get',
        responseType: 'blob' // 关键！必须设置为 blob
    })
}