import Vue from 'vue'
import Router from 'vue-router'
import Inbox from '@/components/Inbox.vue'
import Table from '@/components/Table.vue'
import Projects from '@/components/Projects.vue'
import WeightedVariables from '@/components/WeightedVariables.vue'
import RawPFormula from '@/components/RawPFormula.vue'
import DisplayPFormula from '@/components/DisplayPFormula.vue'
import Login from '@/components/Login.vue'
import CustomAttributes from '@/components/CustomAttributes.vue'
import Boards from '@/components/Boards.vue'

Vue.use(Router)

export default new Router({
  mode: 'history',
  routes: [
    {
      path: '/',
      name: 'Inbox',
      component: Inbox
    },
    {
    	path: '/table',
    	name: 'Table',
    	component: Table
    },
    {
      path: '/boards',
      name: 'Boards',
      component: Boards
    },
    {
      path: '/boards/:board_id',
      name: 'Board',
      component: Table
    },
    {
      path: '/projects',
      name: 'Projects',
      component: Projects
    },
    {
      path: '/weighted-variables',
      name: 'Weighted Variables',
      component: WeightedVariables
    },
    {
      path: '/raw-p-formula',
      name: 'Raw P Formula',
      component: RawPFormula
    },
    {
      path: '/display-p-formula',
      name: 'Display P Formula',
      component: DisplayPFormula
    },
    {
      path: '/login',
      name: 'Login',
      component: Login
    },
    {
      path: '/custom-attributes',
      name: 'Custom Attributes',
      component: CustomAttributes
    },
    {
      path: '*',
      name: '404 Not Found',
      component: null
    }
  ]
})
