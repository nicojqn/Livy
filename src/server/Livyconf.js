// Livy server conf file
module.exports = {
    get: () => {
        LivyConf = {};



        // General

        LivyConf["name"] = "Home";

        LivyConf["port"] = 3000;

        LivyConf["origin"] = "*";





        return LivyConf;
    }
}