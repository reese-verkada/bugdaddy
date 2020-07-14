<template>
	<div class="container">
    <span v-on:click="errors=[]" v-if="errors.length" class="toast error">
        <p v-for="error in errors">
          {{error}}
        </p>
    </span>
    <span v-on:click="success=false" v-if="success" class="toast success">
      <p>{{ success }}</p>
    </span>
    <div class="row" v-if="$route.params.board_id && board.board_name">
      <span class="icon-bookmark"></span>
      <div class="col-sm">
        <h3>{{ board.board_name }}</h3>
        <h5>by {{ board.email || "Unknown" }}</h5>
        <hr>
      </div>
    </div>
		<div class="row">
			<div class="col-sm">
				<input size="35" id="filter" v-model="filterString" type="text" placeholder="Filter issues by string or regex...">
				<span class="tooltip bottom" aria-label="Filters all columns. Match any character or number. Use | for logical OR. Use ^ for matching start of string. Use $ for matching end of string."><span class="icon-help"></span></span>
        <button v-on:click="sync()" class="sync"><span v-bind:class="{'rainbow_text_animated':syncing}">Sync</span></button>
        <button v-on:click="filterByChecked" class="tertiary" v-if="!isEmpty(keyFilter) && !filteringByKeyIsOn">Filter by checked ({{ Object.keys(keyFilter).length }})</button>
        <button v-on:click="filterString = ''; filteringByKeyIsOn = false" v-if="filteringByKeyIsOn" class="secondary">Show all issues</button>
        
        <select v-if="!isEmpty(keyFilter) && !$route.params.board_id" v-model="selectedBoard">
          <option value=0 disabled>Select board</option>
          <option v-for="boardOption in boards" v-bind:value="boardOption.board_id">{{boardOption.board_name}}</option>
        </select>
        <button class="primary" v-if="!isEmpty(keyFilter) && !$route.params.board_id" v-on:click="addToBoard">Add to board ({{Object.keys(keyFilter).length}})</button>

        <button class="secondary" v-if="!isEmpty(keyFilter) && $route.params.board_id" v-on:click="removeFromBoard">Remove from board ({{Object.keys(keyFilter).length}})</button>

        <span v-if="syncErrors.length" class="card error">Sync failed</span>
        <span>{{sortedIssues.length}} {{sortedIssues.length == 1 ? "issue" : "issues"}} displayed</span>
			</div>
		</div>
		<div class="row">
			<div class="col-sm-12">
				<table class="hoverable sticky">
					<thead>
						<tr>
							<th v-for="col in columns" v-on:click="sort(col.id)">
								<span>{{ col.name }}</span>
								<span v-if="sortCol==col.id">{{ sortDirIcon }}</span>
							</th>
              <th v-for="(value, name) in custom_attributes">
                {{name}}<span v-on:click="toggleFilter(name)" v-bind:class="!isEmpty(attrFilters[name]) ? 'icon-filter-on' : 'icon-filter'"></span>
                <div class="attrFilter" v-show="currentlyOpenFilter == name">
                  <fieldset v-for="option in value">
                    <label v-bind:for="`${name}${option}`">{{option}}</label>
                    <input v-bind:checked="attrFilters[name][option]" v-on:change="updateFilter(name,option)" v-bind:id="`${name}${option}`" type="checkbox">
                  </fieldset>
                  <button v-on:click="toggleFilter(name)">Done</button>
                  <button v-on:click="attrFilters[name] = {}">Clear</button>
                </div>
              </th>
              
              <th>Emoji Status</th>
							<th v-if="isAdmin"><input type="checkbox" v-on:click="toggleAllChecked" class="filterCheckbox"> Actions</th>
						</tr>
					</thead>
					<tr @keydown.esc="closeModal(issue.issue_id)" tabindex="0" v-on:dblclick="openModal(issue.issue_id)" v-bind:key="issue.issue_id" v-for="issue in sortedIssues" v-bind:style="{'background-color':issue.color}">
						<td data-label="Key">{{ issue.issue_key }}</td>
						<td data-label="Summary" v-bind:title="issue.summary">{{ issue.summary | truncate }}</td>
						<td data-label="Status">{{ issue.status }}</td>
						<td data-label="Priority">{{ issue.priority }}</td>
						<td data-label="Cases Attached">{{ issue.cases_attached }}</td>
						<td data-label="Total $">{{ issue.total_spend | currency}}</td>
            <td data-label="Updated">{{ issue.updated | fromNowUTC }}</td>
            <td data-label="Created">{{ issue.created | fromNowUTC }}</td>
            <td v-bind:data-label="custom_attribute" v-if="issue_attributes[issue.issue_id]" v-for="(options, custom_attribute) in custom_attributes">{{ issue_attributes[issue.issue_id][custom_attribute] }}</td>
            <td v-else></td>

            <td data-label="Emoji Status">
              <img v-if="issue.emoji == '🔥'" width=30px src="/static/fire.gif">
              <span v-else class="emoji">{{issue.emoji}}</span>
              <img v-if="issue.status == 'Done' || issue.status == 'Closed'" class="gifEmoji" width=30px src="/static/check_mark_button.gif" title="Issue was closed">
              <img v-if="issue.status == 'Reopened'" class="gifEmoji" width=30px src="/static/man_zombie.gif" title="Issue was reopened">
              <img v-if="dateDiff(issue.created, 'months', 6)" class="gifEmoji" width=30px src="/static/clock.gif" title="Issue is older than 6 months">
            </td>

						<td v-if="isAdmin" data-label="Actions">
              <input type="checkbox" v-on:change="keyFilterChange(issue.issue_key,issue.issue_id,$event)" v-model="keyFilter[issue.issue_key]" class="filterCheckbox">
							<a target="_blank" v-bind:href="`${$apiURL}/api/jira_redirect/${issue.issue_key}`" title="Open issue in JIRA"><span class="icon-link"></span></a>
              <label v-on:click="openModal(issue.issue_id)"><span title="Edit issue" class="icon-edit"></span></label>
              <input type="checkbox" v-bind:id="issue.issue_id" class="modal">
              <div>
                <div v-on:dblclick.stop class="card editIssueModal">
                  <label v-on:click="openModal(issue.issue_id)" class="modal-close"></label>
                  <h3 v-bind:style="{'background-color':issue.color}" class="section">{{ issue.issue_key }} {{issue.emoji}}</h3>
                  <EditIssue v-on:saved="sync()" class="section" v-bind:issue="issue" v-bind:issue_attributes="issue_attributes[issue.issue_id]" v-bind:custom_attributes="custom_attributes" v-if="currentIssue == issue.issue_id"/>
                </div>
              </div>
              <span v-on:click="deleteIssue(issue.issue_id)" v-if="!$route.params.board_id" title="Untrack this issue" class="icon-trash"></span>
						</td>
					</tr>
				</table>
			</div>
		</div>
	</div>
</template>

<script>
import axios from 'axios'
import _ from 'lodash'
import moment from 'moment'
import EditIssue from '@/components/EditIssue.vue'

export default {
  name: 'Table',
  components: {
    EditIssue
  },
  data () {
    return {
    	issues:[],
      issue_attributes:{},
      custom_attributes:{},
      suggested_for_deletion:[],
    	syncing:true,
    	columns: [
    		{'id':'issue_key','name':'Key'},
    		{'id':'summary','name':'Summary'},
    		{'id':'status','name':'Status'},
        {'id':'priority','name':'Priority'},
    		//{'id':'display_p','name':'Priority'},
    		//{'id':'raw_p','name':'Raw P'},
    		{'id':'cases_attached','name':'Cases Attached'},
        {'id':'total_spend','name':'Total $'},
        {'id':'updated','name':'Updated'},
        {'id':'created', 'name':'Created'}
    	],
    	sortCol:'priority',
    	sortDir:'asc',
    	sortDirIcon:'▲',
    	filterString:'',
      attrFilters:{},
      syncErrors:[],
      currentIssue:null,
      currentlyOpenFilter:"",
      keyFilter:{},
      filteringByKeyIsOn:false,
      board:{},
      boards:[],
      selectedBoard:0,
      success:false,
      errors:[]
    }
  },
  created() {
  	this.sync()
  },
  props: {
    isAdmin: Boolean
  },
  methods:{
  	sync() {
      this.getData()
      this.syncing = true
  		axios.get(`${this.$apiURL}/api/sync`)
  			.then(resp => {
  				this.syncing = false
          this.syncErrors = resp.data.errors
          this.suggested_for_deletion = []
          if (resp.data.suggested_for_deletion.issues) {
            resp.data.suggested_for_deletion.issues.forEach(i => {
              this.suggested_for_deletion.push(Number(i.id))
            })
          }
  				this.getData()
  			})
        .catch(err => {
          this.syncErrors.push(err)
          this.syncing = false
        })
  	},
  	getData() {
      //if this is a board
      if (this.$route.params.board_id) {
    		axios.get(`${this.$apiURL}/api/boards/${this.$route.params.board_id}`)
    			.then(resp => {
    				this.issues = resp.data.issues
            this.board = resp.data.board
    		})
      } else {
        //this isn't a board, it's the full table
        axios.get(`${this.$apiURL}/api/jira_issues`)
          .then(resp => {
            this.issues = resp.data
            
        })
      } 
      axios.get(`${this.$apiURL}/api/custom_attributes`)
        .then(resp => {
          this.custom_attributes = resp.data.attributes
          for (const attr in this.custom_attributes) {
            this.$set(this.attrFilters, attr, {})
          }
        })
      axios.get(`${this.$apiURL}/api/issue_attributes`)
        .then(resp => {
          this.issue_attributes = resp.data
        })
      axios.get(`${this.$apiURL}/api/boards`)
        .then(resp => {
          this.boards = resp.data.boards
        })
  	},
  	sort(col) {
  		this.sortCol = col
  		this.sortDir = this.sortDir == 'desc' ? 'asc' : 'desc'
  		this.sortDirIcon = this.sortDirIcon == '▼' ? '▲' : '▼'
  	},
    deleteIssue(issue_id) {
      axios.delete(`${this.$apiURL}/api/jira_issues`,{data:[{"issue_id":issue_id}]})
        .then(resp => {
          this.sync()
        })
    },
    openModal(id,e) {
      this.currentIssue = id
      document.getElementById(id).click()
      document.body.classList.toggle("modal-open")
    },
    closeModal(id) {
      this.currentIssue = null
      document.body.classList.remove("modal-open")
      document.getElementById(id).checked = false
    },
    toggleFilter(name) {
      if (this.currentlyOpenFilter == name) {
        this.currentlyOpenFilter = ""
      }
      else {
        this.currentlyOpenFilter = name
      }
    },
    updateFilter (name, option) {
      if (this.attrFilters[name] && this.attrFilters[name][option]) {
        this.$delete(this.attrFilters[name], option)
      } else {
        this.$set(this.attrFilters[name],option,true)
      }
    },
    isEmpty(thing) {
      return _.isEmpty(thing)
    },
    keyFilterChange(key, id, event) {
      if (event.srcElement.checked) {
        this.$set(this.keyFilter, key, id)
      } else {
        this.$delete(this.keyFilter, key)
      }
    },
    filterByChecked() {
      this.filterString = "^"
      this.filterString += Object.keys(this.keyFilter).join("$|^")
      this.filterString += "$"
      this.filteringByKeyIsOn = true
    },
    dateDiff(date, measurement, value) {
      return moment.utc().diff(moment.utc(date), measurement) >= value
    },
    toggleAllChecked(event) {
      this.sortedIssues.forEach(issue => {
        if (event.target.checked) {
          this.$set(this.keyFilter, issue.issue_key, issue.issue_id)
        } else {
          this.keyFilter = {}
        }        
      })
    },
    addToBoard(event) {
      if (this.selectedBoard > 0) {
        this.success = false
        this.errors = []
        let issues = []
        for (const issue in this.keyFilter) {
          issues.push(this.keyFilter[issue])
        }
        axios.post(`${this.$apiURL}/api/boards/${this.selectedBoard}`,{'issues':issues})
          .then(resp => {
            this.success = "Added " + issues.length + " issues to board"
          })
          .catch(err => {
            if (err.response && err.response.data) {
              this.errors = err.response.data.errors
            } else {
              this.errors.push(err)
            }
          })
      }
    },
    removeFromBoard(event) {
      this.success = false
      this.errors = []
      let issues = []
      for (const issue in this.keyFilter) {
        issues.push(this.keyFilter[issue])
      }
      axios.delete(`${this.$apiURL}/api/boards/${this.$route.params.board_id}`,{data:{'issues':issues}})
        .then(resp => {
          this.success = "Removed " + issues.length + " issues from board"
          this.issues = resp.data.issues
          this.keyFilter = {}
        })
        .catch(err => {
          if (err.response && err.response.data) {
            this.errors = err.response.data.errors
          } else {
            this.errors.push(err)
          }
        })
    }
  },
  filters: {
  	truncate(text) {
  		if (text == null) {
        text = ''
      }
      return text.length <= 60 ? text : text.substring(0,60) + "..."
  	},
    currency(amount) {
      if (typeof amount !== "number") {
        return amount
      }
      return '$' + amount.toFixed(2).replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,')
    },
    dateUTC(date) {
      return moment.utc(date).format("YYYY-MM-DD")
    },
    fromNowUTC(date) {
      return moment.utc(date).fromNow()
    }
  },
  computed: {
    isAttrFilterOn() {
      for (const attr in this.attrFilters) {
        for (const option in this.attrFilters[attr]) {
          if (this.attrFilters[attr][option] === true) {
            return true
          }
        }
      }
      return false
    },
  	sortedIssues() {
  		return _.orderBy(this.issues,this.sortCol,this.sortDir)
  			.filter(issue => {
          if (this.isAttrFilterOn) { //If we're filtering by at least one attribute
            if (this.issue_attributes[issue.issue_id]) { //If the issue has at least one attribute set
              for (const attr in this.attrFilters) { //Go through every checked filter
                if (!_.isEmpty(this.attrFilters[attr])) {
                  if (this.issue_attributes[issue.issue_id][attr]) {  //Issue has this attr set and none of the options match
                    if (!(this.issue_attributes[issue.issue_id][attr] in this.attrFilters[attr])) {
                      return false
                    } else { //if an option does match, the option needs to = true
                      if (this.attrFilters[attr][this.issue_attributes[issue.issue_id][attr]] !== true) {
                        return false
                      }
                    }
                  } else { //Issue doesn't have attr set at all
                    return false
                  }
                }
              }
            } else { //If the issue doesn't have any attributes set, hide it (since it obvi won't match the filter)
              return false
            }
          }

  				for (const col in issue) {
  					if (RegExp(this.filterString.toLowerCase()).test(String(issue[col]).toLowerCase())) {
  						return true
  					}
  				}
  			})
  	}
  },
  watch: {
    $route(to, from) {
      if (to.params.board_id != from.params.board_id) {
        this.getData()
      }
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
  .error {
    background-color: #d32f2f;
  }
  .success {
    background-color: #bada55;
  }
  .filterCheckbox {
    height: 10px;
  }
	table {
		max-height: inherit;
    overflow: visible;
	}
	td, th {
		font-size: 75%;
		padding: 5px;
	}
  td {
    background-color: inherit;
  }
  span[class^=icon-] {
    font-size: 1rem;
  }
	.icon-edit {
    cursor: pointer;
  }
  .icon-trash {
    cursor: pointer;
    background-image: url('/static/trash.svg');
  }
  .icon-filter {
    cursor: pointer;
    background-image: url('/static/filter.svg');
  }
  .icon-filter-on {
    cursor: pointer;
    background-image: url('/static/filter-on.svg');
  }
  .icon-bookmark {
    font-size: 5rem !important;
  }
	.editIssueModal {
    max-width:90%;
    max-height: 80vh !important;
    text-align: left;
    border: 0;
    border-radius: 15px;
    box-shadow: #555 0px 0px 30px;
  }
  span.card {
    display: inline;
  }
  .tooltip:after {
    white-space: normal;
    width: 300px;
  }
  .emoji {
    font-size: 1.5rem;
  }
  .gifEmoji {
    vertical-align: sub;
  }
  .rainbow_text_animated {
    background: linear-gradient(to right, #6666ff, #0099ff , #00ff00, #ff3399, #6666ff);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    animation: rainbow_animation 1s ease-in-out infinite;
    background-size: 400% 100%;
  } 
  @keyframes rainbow_animation {
      0%,100% {
          background-position: 0 0;
      }

      50% {
          background-position: 100% 0;
      }
  }
  button.sync:focus {
    outline: none;
  }
  .attrFilter {
    background-color: white;
    position: absolute;
    border-radius: 8px;
    box-shadow: rgba(0, 0, 0, 0.043) 0px 3px;
  }
  .attrFilter fieldset {
    border-radius: inherit;
  }
</style>
