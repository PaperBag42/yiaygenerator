const path = require('path');


module.exports = {
	context: __dirname,
	entry: './yiaygenerator/static/js/index',
	
	output: {
		path: path.resolve('./yiaygenerator/static/bundles/'),
		filename: '[name].js',
	},
	
	module: {
		rules: [
			{
				test: /\.js$/,
				exclude: /node_modules/,
				loader: 'babel-loader',
			},
		],
	},
};
