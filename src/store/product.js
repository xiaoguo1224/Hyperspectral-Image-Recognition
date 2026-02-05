import {defineStore} from "pinia";
import {computed, ref} from "vue";

export const useProductStore = defineStore('product', () => {
    const list = ref([])


    const totalPrice = computed(() => {
        return list.value.reduce((total, now) => {
            total += now.price
        }, 0)
    })

    async function getProduct() {
        const res = await fetch('/product.json')
        const data = await res.json()
        list.value = data.list
        console.log("pinia" + list.value)
    }

    function setProduct(product) {
        list.value.push(product)
    }

    return {
        list,
        totalPrice,
        getProduct,
        setProduct,
    }
})
