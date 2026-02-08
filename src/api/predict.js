import request from '@/utils/request'

export function predict(data) {
    return request({
        url: '/detection/predict',
        method: 'post',
        data: data
    })
}

export function getList(data) {
    return request({
        url: '/detection/getList',
        method: 'get',
        data: data
    })
}

export function evaluate(data) {
    return request({
        url: '/detection/evaluate',
        method: 'post',
        data: data
    })
}

