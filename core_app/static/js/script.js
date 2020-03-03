let user_menu = new Vue({
    el: '#user-menu',
    created() {
        axios.get('/api/students/').then((response) => {
            this.students = response.data;
        });
        axios.get('/api/students/last/').then((response) => {
            this.currentStudent = response.data;
        });
    },
    data: {
        currentStudent: { name: 'Student 1', id: 1 },
        students: []
    }
})