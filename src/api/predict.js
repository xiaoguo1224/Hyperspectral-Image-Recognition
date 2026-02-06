import request from '@/utils/request'

export function predict(data) {
    return request({
        url: '/detection/predict',
        method: 'post',
        data: data
    })
}
