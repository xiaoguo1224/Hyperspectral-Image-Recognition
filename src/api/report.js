import request from '@/utils/request'

export function cubeView(data) {
    return request({
        url: '/report/cube',
        method: 'post',
        data: data
    })
}