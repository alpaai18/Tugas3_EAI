import graphene
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_graphql import GraphQLView
from functools import wraps
from graphene_sqlalchemy import SQLAlchemyObjectType

app = Flask(__name__)

'''

graphene                            = digunakan untuk membuat schema GraphQL baik dalam bentuk query ataupun Mutation

Flask                               = digunakan untuk membuat aplikasi web
Jsonify                             = digunakan untuk mengembalikan data dalam format json
request                             = digunakan untuk merespons permintaan dari HTTP

wraps                               = membuat decorator (fungsi yang mengubah fungsi lain dengan menambahkan fungsionalitas 
                                      sebelum atau sesudah digunakan)

SQLAlchemy                          = digunakan untuk interaksi dengan database menggunakan ORM
GraphQLView                         = digunakan untuk menambahkan endpoint GraphQL ke aplikasi Flask, contoh localhost:5000/graphql
SQLAlchemyObjectType                = membuat tipe objek GraphQL

app                                 = variabel yang menampung instance yang akan menjadi aplikasi web Flask nya, contoh app.run app.config
'''

#####################################################################################################################################################

service_db_url  = "mysql://avnadmin:AVNS_eRL_b1tVr30hta8rpoi@mysql-2c5aaac4-tugas-2-dwbi.a.aivencloud.com:17390/tugas3_eai"
user_db         = "avnadmin"
password_db     = "AVNS_eRL_b1tVr30hta8rpoi"
host            = "mysql-2c5aaac4-tugas-2-dwbi.a.aivencloud.com"
port            = "17390"
database        = "tugas3_eai"

app.config['SQLALCHEMY_DATABASE_URI'] = service_db_url
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {
        'ssl': {
            'ssl_mode': 'REQUIRED'
        }
    }
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

'''
Baris 29 - 34                       = Konfigurasi Database, Detail nya bisa dilihat di platform database masing masing
'SQLALCHEMY_DATABASE_URI'           = Mengatur URI yang akan dipakai komunikasi antara SQLAlchemy dengan MySQL
'SQLALCHEMY_ENGINE_OPTIONS'         = koneksi tambahan (SSL) agar komunikasi lebih aman

'SQLALCHEMY_TRACK_MODIFICATIONS'    = untuk SQLAlchemy melacak perubahan, kalau True gaperlu menambahkan db.add() db.commit() ; 
                                      tapi bisa berpengaruh ke kinerja

db                                  = Objek SQLAlchemy untuk berinteraksi dengan database yang kita miliki
'''
#####################################################################################################################################################

# Model
class Jabatan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    posisi = db.Column(db.String(80), nullable=False)

with app.app_context():
    db.create_all()

'''
Model Jabatan                       = model SQLAlchemy untuk mewakili tabel jabatan di database
app.app_context()                   = untuk membuat sebuah konteks atau akses ke aplikasi yang aktif
db.create_all()                     = disini dilakukan pembuatan database dengan tabel jabatan dan nama database sesuai dengan
                                      yang di definisikan sebelumnya
'''

#####################################################################################################################################################

# Authentication Function
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token Autentikasi Tidak Ditemukan'}), 403
        
        # Token validation process
        return f(*args, **kwargs)
    return decorated

'''
def token_required(f)               = fungsi yang menerima fungsi f sebagai argumen dan mengembalikan fungsi baru pengganti fungsi decorated
wraps(f)                            = untuk memastikan fungsi decorated memiliki metadata (nama fungsi, argumen, dan parameter) sama dengan
                                      fungsi yang didekorasi(fungsi f)
def decorated                       = fungsi penengah untuk melakukan pengecekan apakah ada token atau tidak. dan akan menerima arguments (*args)
                                      dan keyword (**kwargs) yang sama seperti fungsi asli
token                               = variabel yang menampung token otentikasi

'''

# GraphQL Schema
class JabatanType(SQLAlchemyObjectType):
    class Meta:
        model = Jabatan

# Query Class
class Query(graphene.ObjectType):
    jabatan_by_id = graphene.Field(JabatanType, id=graphene.Int(required=True))
    jabatan_by_posisi = graphene.Field(JabatanType, posisi=graphene.String(required=True))
    banyak_jabatan = graphene.List(JabatanType)

    def resolve_jabatan_by_id(self, info, id):
        return Jabatan.query.get(id)
    
    def resolve_jabatan_by_posisi(self, info, posisi):
        return Jabatan.query.filter_by(posisi=posisi).first()
    
    def resolve_banyak_jabatan(self, info):
        return Jabatan.query.all()

# Mutation Schema
class CreateJabatan(graphene.Mutation):
    id = graphene.Int()
    posisi = graphene.String()

    class Arguments:
        posisi = graphene.String(required=True)

    def mutate(self, info, posisi):
        if not posisi:
            raise ValueError("Kolom Nama Masih Kosong!")
        
        posisi_baru = Jabatan(posisi=posisi)
        db.session.add(posisi_baru)
        db.session.commit()
        return CreateJabatan(id=posisi_baru.id, posisi=posisi_baru.posisi)

class UpdateJabatan(graphene.Mutation):
    id = graphene.Int(required=True)
    posisi = graphene.String()

    class Arguments:
        id = graphene.Int(required=True)
        posisi = graphene.String()

    @token_required
    def mutate(self, info, id, posisi=None):
        jabatan = Jabatan.query.get(id)
        if not jabatan:
            raise Exception("Data Tidak Ditemukan!")
        
        if posisi:
            jabatan.posisi = posisi
        
        db.session.commit()
        return UpdateJabatan(id=jabatan.id, posisi=jabatan.posisi)
    
class DeleteJabatan(graphene.Mutation):
    id = graphene.Int()

    class Arguments:
        id = graphene.Int(required=True)
    
    @token_required
    def mutate(self, info, id):
        jabatan = Jabatan.query.get(id)
        if not jabatan:
            raise Exception("Data Tidak Ditemukan!")

        db.session.delete(jabatan)
        db.session.commit()
        return DeleteJabatan(id=id)

# Mutation Class
class Mutation(graphene.ObjectType):
    create_jabatan = CreateJabatan.Field()
    update_jabatan = UpdateJabatan.Field()
    delete_jabatan = DeleteJabatan.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

# GraphQL Endpoint
app.add_url_rule('/graphql', view_func=token_required(GraphQLView.as_view('graphql', schema=schema, graphiql=True)))

if __name__ == '__main__':
    app.run(debug=True)

'''
@token_required                         = akan menjalankan fungsi token_required untuk memastikan 
                                          hanya user terauthentikasi yang bisa mengakses command
db.session.___  & db.session.commit     = konsepnya sama kayak di github, setelah melakukan sesuatu kita commit 

'''