<template>
  <div class="container">
    <button v-on:click="getData()" class="refresh">Refresh Inbox</button>
    <div class="row">
      <div class="col-md-1"></div>
      <div class="col-sm">
        <div v-if="!changes.length" class="row inboxitem zero">
          <div class="col-sm">
            <h1>Inbox at zero; you're my superhero!</h1>
            <img src="/static/beach-vacation.svg">
          </div>
        </div>
        <div v-if="changes.length" class="row inboxitem inboxheader">
          <div class="col-sm">
            <h1 v-if="changes.length > 1"><span class="icon-mail"></span> {{ changes.length }} changes in your inbox</h1>
            <h1 v-if="changes.length == 1"><span class="icon-mail"></span> 1 change in your inbox</h1>
            <p>The {{this.$appName}} inbox notifies you of any recent changes to issues.</p>
          </div>
          <div class="col-sm-3">
            <button class="hugeButton secondary" v-on:click="dismiss">Dismiss All</button>
          </div>
        </div>
        <div class="inboxitem" v-for="change in changes">
          <h4 class="title">
            <a v-bind:href="`${$apiURL}/api/jira_redirect/${change.issue_key}`" target="_blank">
              <span class="issue_key">{{ change.issue_key }}</span>
              <span> - </span>
              <span class="summary">{{ change.summary }}</span>
            </a>
          </h4>
          <hr>
          <div class="row">
            <div class="detail card fluid" v-for="item in change.changes">
            <span class="bold field">{{ item.field }}</span>
            <div>
              <span class="old">{{item.old}}</span>
              <span class="arrow">&rarr;</span>
              <span class="new">{{item.new}}</span>
            </div>
          </div>
          </div>
        </div>
      </div>
      <div class="col-md-1"></div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import EditIssue from '@/components/EditIssue.vue'

axios.defaults.withCredentials = true

export default {
  name: 'Inbox',
  components: {
    EditIssue
  },
  data () {
    return {
     currentIssue:null,
     changes:[]
    }
  },
  created() {
    this.getData()
  },
  methods: {
    getData() {
      this.currentIssue = null
      axios.get(`${this.$apiURL}/api/concierge`)
        .then(resp => {
          this.changes = resp.data
      })
    },
    dismiss() {
      let change_id = this.changes[0].change_id
      axios.post(`${this.$apiURL}/api/seen_change`,{'seen_change':change_id})
        .then(resp => {
          this.getData()
        })
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
  .inboxitem {
    box-shadow: rgba(0, 0, 0, 0.043) 0px 3px;
    border-radius: 8px;
    background-color: white;
    padding: 5px;
    margin: 10px 0;
  }
  .zero img{
    margin: 0 auto;
    display: block;
  }
  .zero {
    background: rgb(255,255,255);
    background: linear-gradient(0deg, rgba(255,255,255,1) 50%, rgba(74,208,254,1) 100%);
    color: white;
  }
  .refresh {
    position: fixed;
    bottom: 25px;
    right: 25px;
    z-index: 100;
  }
  .editissuebutton:hover {
    border-width: 1px;
    border-color: #0288d1;
    border-style: solid;
  }
  .editissuelabel:hover {
    cursor: pointer;
  }
  .editIssueModal {
    max-width:90%;
  }
  .hugeButton {
    margin: 0;
    padding: 0;
    height: 100%;
    width: 100%;
    border-radius: 8px;
  }
  .detail {
    box-shadow: rgba(0, 0, 0, 0.043) 0px 3px;
    border-radius: 8px;
    background-color: white;
    padding: 15px;
    margin: 10px !important;
  }
  .bold {
    font-weight: bold;
  }
  .field {
    text-transform: capitalize;
  }
  .old {
    background-color: rgba(252, 236, 231, 1);
    padding: 5px;
  }
  .new {
    background-color: rgba(232, 251, 240, 1);
    padding: 5px;
  }
</style>
