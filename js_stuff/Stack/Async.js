
async.parallel(['file1', 'file2', 'file3'], fs.stat, function (err, results) {
    // results is now an array of stats for each file
})

// The code above performs the samething as the code below


function stats (file) {
  return new Promise((resolve, reject) => {
    fs.stat(file, (err, data) => {
      if (err) {
        return reject (err)
      }
      resolve(data)
    })
  })
}

Promise.all([
  stats('file1'),
  stats('file2'),
  stats('file3')
])
.then((data) => console.log(data))
.catch((err) => console.log(err))
