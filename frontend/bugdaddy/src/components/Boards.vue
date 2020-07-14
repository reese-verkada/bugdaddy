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
    <div class="row">
      <input placeholder="Filter boards by name or email..." size="50" v-model="filterString" id="filterString">
    </div>
    <div class="row">
      <div class="card">
        <div class="section">
          <h3>Add Board</h3>
          <input placeholder="Board name" v-model="newBoard.board_name" size="30">
        </div>
        <div class="section">
          <button v-on:click="addBoard" class="primary">Add</button>
        </div>
      </div>

      <div class="card" v-for="board,index in sortedBoards">
        <div class="section">
          <h3><a v-bind:href="`/boards/${board.board_id}`">{{board.board_name}}</a></h3>
          <h4>by {{board.email || "Unknown"}}</h4>
        </div>
        <div class="section">
          <button class="secondary" v-on:click="deleteBoard(board, index)">Delete</button>
          <button class="tertiary" v-on:click="$set(boards[index], 'editMode', !board.editMode)">Edit</button>
          <input v-model="board.board_name" v-if="board.editMode" v-on:blur="editBoardName(board)">
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Boards',
  data() {
    return {
      errors: [],
      boards: [],
      newBoard: {},
      success: false,
      filterString: ''
    }
  },
  created() {
    this.getData()
  },
  updated() {
  },
  methods: {
    getData() {
      this.errors = []
      this.success = false
      axios.get(`${this.$apiURL}/api/boards`)
        .then(resp => {
          this.boards = resp.data.boards
        })
        .catch(err => {
          this.errors = resp.data.errors
        })
    },
    addBoard() {
      this.success = false
      this.errors = []
      if (this.newBoard.board_name) {
        axios.post(`${this.$apiURL}/api/boards`,this.newBoard)
          .then(resp => {
            this.boards = resp.data.boards
            this.success = "Added board " + this.newBoard.board_name
            this.newBoard = {}
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
    editBoardName(board) {
      this.success = false
      this.errors = []
      if (board.board_name) {
        board.editMode = false
        axios.post(`${this.$apiURL}/api/boards/${board.board_id}`,{'board_name':board.board_name})
          .then(resp => {
            this.success = "Changed board name to " + board.board_name
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
    deleteBoard(board, index) {
      this.success = false
      this.errors = []
      axios.delete(`${this.$apiURL}/api/boards/${board.board_id}`)
        .then(resp => {
          this.$delete(this.boards, index)
          this.success = "Deleted board " + board.board_name
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
  computed: {
    sortedBoards() {
      return this.boards.filter(board => {
        for (const col in board) {
          if (RegExp(this.filterString.toLowerCase()).test(String(board[col]).toLowerCase())) {
            return true
          }
        }
      })
    }
  }
}
</script>

<style>
  .error {
    background-color: #d32f2f;
  }
  .success {
    background-color: #bada55;
  }
</style>
