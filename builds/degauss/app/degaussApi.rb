# gaia.rb - simpel API for the degauss geocoder
require 'sinatra'
require 'rubygems'
require 'geocoder/us'
require 'json'

db = Geocoder::US::Database.new("/opt/geocoder.db")

get '/' do
  'API for degauss geocoder'
end

get '/geocode/:address' do
  out = db.geocode(ARGV[0])
  $stdout.puts out.to_json
end